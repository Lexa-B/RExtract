from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.schema.runnable.passthrough import RunnableAssign
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, FunctionMessage, ToolMessage
import ast
import json

################################################################################
## Definition of RExtract
def RExtract(pydantic_class, llm, prompt):
    '''
    Runnable Extraction module 
    Returns a knowledge dictionary populated by slot-filling extraction
    '''
    expected_keys = set(pydantic_class.model_fields.keys())

    def gen_format_instructions(x):
        parser = PydanticOutputParser(pydantic_object=pydantic_class)
        format_schema = parser.get_output_jsonschema()
        # Get example from the model's schema if available
        try:
            example = pydantic_class.model_config['json_schema_extra']['examples'][0]
        except:
            example = None                    
        format_instructions = (
            "Your output should be formatted and structured as per this schema:\n"
            f"{format_schema['properties']}\n\n"
            "Do not copy the schema in your output, just use it to format your generated output. "
            "Your output should be formatted as a JSON object, with no other text or formatting. "
        )
        if example:
            format_instructions += (
                f"Here is an example of the output:\n"
                f"{example}\n\n"
            )
        return format_instructions
    
    instruct_merge = RunnableAssign({'format_instructions' : gen_format_instructions})

    def prompt_recorder(prompt):
        record = []
        for m in prompt.messages:
            if isinstance(m, HumanMessage):
                record.append(f"Human: {m.content}")
            elif isinstance(m, SystemMessage):
                record.append(f"System: {m.content}")
            elif isinstance(m, AIMessage):
                record.append(f"AI: {m.content}")
            elif isinstance(m, FunctionMessage):
                record.append(f"Function: {m.content}")
            elif isinstance(m, "ToolMessage"):
                record.append(f"Tool: {m.content}")
            else:
                record.append(str(m))
        return record

    llm_process = RunnableLambda(
        lambda x: {
            'prompt' : prompt_recorder(x),
            'llm_output' : llm.invoke(x)
        }
    )
    
    def preparse(string):
        # Convert AIMessage to string if needed
        if hasattr(string, 'content'):
            string = string.content

        if '{' not in string: string = '{' + string
        if '}' not in string: string = string + '}'
        
        # Clean up the string
        string = (string
            .replace("\\_", "_")
            .replace("\n", " ")
            .replace(r"\]", "]")
            .replace(r"\[", "[")
        )
        
        # print("Raw string:", string) ##DEBUG: Uncomment to see the raw string
        
        try:
            # Try to parse as direct JSON first
            data = ast.literal_eval(string)
            
            # If we have a properties wrapper, extract it
            if isinstance(data, dict) and "properties" in data:
                data = data["properties"]
                
            # Convert back to string
            string = json.dumps(data, ensure_ascii=False)
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # If JSON parsing fails, try to extract just the JSON object
            import re
            match = re.search(r'\{[^{}]*\}', string)
            if match:
                string = match.group(0)
            
            # Try to clean up the string
            string = (string
                .replace('\n', '')
                .replace('  ', ' ')
                .strip()
            )
            
        # print("Processed string:", string) ##DEBUG: Uncomment to see the processed string
        return string
    
    def parser(state):
        llm_output = state['llm_output']
        try:
            preparsed_output = preparse(llm_output)
            parsed_output = PydanticOutputParser(pydantic_object=pydantic_class).parse(preparsed_output)
            if set(parsed_output.model_fields.keys()) == expected_keys:
                return parsed_output
            else:
                error = {
                    "type":"LLM output fields do not match expected fields",
                    "details":f"Fields do not match: {parsed_output.keys()} != {pydantic_class.model_fields.keys()}"
                }
        except Exception as e:
            error = {
                "type":"Error parsing LLM output",
                "details": e
            }
        if error:
            state["error"] = error
        return state
    
    error_prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are the debugger for another LLM model. You will be given that model's original prompt as well as its broken output. "
            "The output has already been flagged by the parser as having an error. "
            "Your task is to attempt to fix the LLM's output to be parsable based on the prompt and the parser's error message.\n"
            "The original prompt is:\n\"{prompt}\"\n\n"
            "The original output is:\n\"{llm_output}\"\n\n"
            "The error message is:\n\"{error}\"\n\n"
            "Do not explain your reasoning, just respond with the corrected output. "
            "Do not include any other text or formatting such as quotes or backticks. "
            "The entire contents of your response must be one valid JSON object that can be parsed by the Pydantic parser. "
            "Use double quotes for all property names and string values in the JSON output."
            ))
    ])
    def error_handler(state):
        if isinstance(state, pydantic_class): # If the state is a conforms to the pydantic class, then everything is already done in RExtract
            return state
        try:
            if state['error']: # If there is an error, we need to try to fix it
                i = 0      
                while state['error'] and (i < 3):
                    pprint(f"Running error handler due to error: {state['error']}")
                    i += 1
                    try:
                        # Get corrected output from error chain
                        corrected_output = error_chain.invoke({
                            "prompt": state['prompt'],
                            "llm_output": state['llm_output'],
                            "error": state['error']
                        })
                        
                        # Convert string to dict if needed
                        if isinstance(corrected_output, str):
                            corrected_output = json.dumps(ast.literal_eval(corrected_output))
                        
                        state['llm_output'] = corrected_output
                        
                        # Try parsing the corrected output
                        try:
                            parsed_output = json.loads(state['llm_output'])
                            # Check if the corrected output has the right keys
                            if set(parsed_output.keys()) == set(['running_summary', 'main_ideas', 'loose_ends']):
                                state['error'] = None  # Clear error if keys match
                            else:
                                state['error'] = {
                                    "type": "LLM output fields do not match expected fields",
                                    "details": f"Fields do not match: {parsed_output.keys()} != {expected_keys}"
                                }
                        except Exception as e:
                            state['error'] = {
                                "type": "Error parsing corrected LLM output",
                                "details": e
                            }
                            
                    except Exception as e:
                        state['error'] = {
                            "type": "Error with error-handling LLM output",
                            "details": e
                        }
                        break
                try:
                    state = PydanticOutputParser(pydantic_object=pydantic_class).parse(state['llm_output'])
                    return state
                except:
                    state['error'] = {
                        "type": "Error with error-handling LLM output",
                        "details": "Error-handler fixed the error, but the output does not conform to the specified class"
                    }
                    return state
            else:
                state['error'] = {
                    "type": "Error with RExtract state",
                    "details": "Error attribute not found in RExtract state, but does not conform to the specified class"
                }
                return state
        
        except:
            state['error'] = {
                "type": "Error with RExtract state",
                "details": "Error attribute not found in RExtract state, but does not conform to the specified class"
            }
            return state
    

    main_chain = (
        instruct_merge
        | prompt
        | llm_process
        | parser
        | error_handler
    )

    error_chain = (
        error_prompt 
        | llm 
        | StrOutputParser()
    )

    return main_chain
