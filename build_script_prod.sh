docker build -t backend_app .
##
docker save -o backend_app.tar backend_app
gzip backend_app.tar
sudo scp -r -i permit.pem backend_app.tar.gz ubuntu@ec2-18-117-143-56.us-east-2.compute.amazonaws.com:/home/ubuntu
send "yes"
ls -s
ssh -t -i permit.pem find_permit@find-permit.westus2.cloudapp.azure.com 'sudo docker  run -d -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.10.2'
echo 'DONE'
ssh -t find_permit@find-permit.westus2.cloudapp.azure.com 'sudo docker load -i backend_app.tar && sudo docker run -t -p 5000:5000 backend_app'
echo 'DONE'
#
#
# ssh find_permit@find-permit.westus2.cloudapp.azure.com