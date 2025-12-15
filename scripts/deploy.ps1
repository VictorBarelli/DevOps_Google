param (
    [string]$ProjectId
)

if (-not $ProjectId) {
    $ProjectId = Read-Host "Please enter your Google Cloud Project ID"
}

if (-not $ProjectId) {
    Write-Error "Project ID is required."
    exit 1
}

$Region = "us-central1"
$RepoName = "todo-repo"
$ServiceName = "todo-api"
$ImageName = "$Region-docker.pkg.dev/$ProjectId/$RepoName/todo-app:latest"

Write-Host "Setting project to $ProjectId..."
gcloud config set project $ProjectId

Write-Host "Enabling services (if not enabled via Terraform yet)..."
gcloud services enable artifactregistry.googleapis.com run.googleapis.com

Write-Host "Initializing Terraform..."
cd ..\terraform
terraform init
terraform apply -var="project_id=$ProjectId" -auto-approve

Write-Host "Authenticating Docker with Artifact Registry..."
gcloud auth configure-docker "$Region-docker.pkg.dev" --quiet

Write-Host "Building Docker image..."
cd ..\app
docker build -t $ImageName .

Write-Host "Pushing Docker image to Artifact Registry..."
docker push $ImageName

Write-Host "Updating Cloud Run service with new image..."
gcloud run deploy $ServiceName --image $ImageName --region $Region --allow-unauthenticated

Write-Host "Deployment Complete!"
