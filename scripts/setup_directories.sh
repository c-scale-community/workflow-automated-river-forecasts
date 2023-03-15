
PROJECT_HOME=/project/lsda

mkdir -p -m775 $PROJECT_HOME/{Data/{forcing/{converted,downloaded},model_input,model_output,logs},Public,Software,Share/home}

# Git CLONE to $PROJECT_HOME/Software
# Clone to GitHub folder, in order to copy correct files (with PROJECT_HOME) in the Software folder
git clone https://github.com/c-scale-community/use-case-high-res-land-surface-drought-analysis.git $PROJECT_HOME/Software/GitHub

# Copy contents from GitHub folder to Software folder
cp -a $PROJECT_HOME/Software/GitHub/. $PROJECT_HOME/Software

# Replace project home in scripts with real project home
# sed -i "s|^PROJECT_HOME=to_be_modified|PROJECT_HOME=$PROJECT_HOME|" "$PROJECT_HOME/Software/scripts/prepare.sh"
# sed -i "s|^PROJECT_HOME=to_be_modified|PROJECT_HOME=$PROJECT_HOME|" "$PROJECT_HOME/Software/scripts/wflow_catchup.sh"
# sed -i "s|^PROJECT_HOME=to_be_modified|PROJECT_HOME=$PROJECT_HOME|" "$PROJECT_HOME/Software/scripts/wflow_batch.sh"
# sed -i "s|^PROJECT_HOME=to_be_modified|PROJECT_HOME=$PROJECT_HOME|" "$PROJECT_HOME/Software/scripts/plotting.sh"
sed -i "s|^PROJECT_HOME=to_be_modified|PROJECT_HOME=$PROJECT_HOME|" "$PROJECT_HOME/Software/scripts/workflow.sh"

### ADD WFLOW IMAGE

### BUILD PYTHON IMAGE

### ADD CDSKEY FILE IN $PROJECT_HOME/Share/home/.cdsapirc