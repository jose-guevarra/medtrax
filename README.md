# Medtrax
Personal Health Records app


- Create RAG app or agent or both
- create front end
- find a data set (my health records)
- Ingest records
- evaluate performance (mention criteria)
- collect user feedback and monitor app
- add app preview in video form
- 



https://github.com/jose-guevarra/llm-zoomcamp/blob/main/project.md


# Bootstrap

pip3 install uv
sudo dnf install python3.14-pip

curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash -
sudo dnf install -y nodejs


cd infra/medtrack

sudo npm install 
npx cdk --version


# Run
uv sync
uv run npx cdk synth



# Deploy Instructions

# Step 1

cd infra/mtx
terraform init
terraform plan
terraform apply

* This will fail due to no ECR image

# Step 2 - Build initial image
cd infra/mtx/tools
sh upload-agent-to-ecr.sh

* This builds and uploads agent image to ECR

# Step 3 - ReDploy
terraform apply

When successfuly, take note of Output values of deployed resource.


# Web app
uv run streamlit run app.py