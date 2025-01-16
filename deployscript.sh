## Run the followign in git bash:
# chmod +x deployscript.sh
# ./deployscript.sh

# Build and push Docker images
echo "Switching to web Dockerfile and pushing the web image..."
mv Dockerfile.web Dockerfile
heroku container:push web --app scoritoodds
if [ $? -ne 0 ]; then
  echo "Failed to push the web image. Exiting."
  mv Dockerfile Dockerfile.web
  exit 1
fi
mv Dockerfile Dockerfile.web

echo "Switching to worker Dockerfile and pushing the worker image..."
mv Dockerfile.worker Dockerfile
heroku container:push worker --app scoritoodds
if [ $? -ne 0 ]; then
  echo "Failed to push the worker image. Exiting."
  mv Dockerfile Dockerfile.worker
  exit 1
fi
mv Dockerfile Dockerfile.worker

# Release the images
echo "Releasing the web image..."
heroku container:release web --app scoritoodds
if [ $? -ne 0 ]; then
  echo "Failed to release the web image. Exiting."
  exit 1
fi

echo "Releasing the worker image..."
heroku container:release worker --app scoritoodds
if [ $? -ne 0 ]; then
  echo "Failed to release the worker image. Exiting."
  exit 1
fi
echo "Successfully deployed web and worker images to Heroku!"

