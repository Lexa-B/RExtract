chmod u+x "$(dirname "$0")"/**/*.sh
read -p "Delete old virtual environment - Continue (y/n)?" choice
if [ "$choice" = "y" ]; then
  echo "REMOVING...";
  rm -rf ./VenvLx
  read -p "Create new virtual environment - Continue (y/n)?" choice
  if [ "$choice" = "y" ]; then
    echo "BUILDING...";
    python3.12 -m venv ./VenvLx
  fi
fi


