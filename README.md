# RExtract

This python script is a tool for extracting information from passed text using a LLM. It accepts a pydantic class definition and a prompt. It then uses the LLM to extract the information from the text and return a Pydantic object of the information.

## Installation

```bash
pip install -r requirements.txt
```
## Usage

```python
from rextract import RExtract
from pydantic import BaseModel
from langchain_core.llms import BaseLLM
from langchain_core.prompts import ChatPromptTemplate
```

Define your Pydantic model
```python
class YourModel(BaseModel):
field1: str
field2: str
```
Create your prompt
```python
prompt = ChatPromptTemplate.from_messages([
("system", "Your system message"),
("human", "Your human message")
])
```
Initialize your LLM
```python
llm = YourLLM()
```
Create extractor
```python
extractor = RExtract(YourModel, llm, prompt)
```
Run extraction
```python
result = extractor.invoke({"your": "input"})
```