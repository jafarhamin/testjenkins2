#!/bin/bash
set -x
set -e

#artifactory=10.131.69.114
repo=http://aww.dsl.alcatel.be/ftp/pub/outgoing/ESAM/DAILY
repo1=http://artifactory-espoo-fnms.int.net.nokia.com:8081/artifactory/incoming-nv-device-extensions_local/bba/
artifactory=artifactory-espoo-fnms.int.net.nokia.com
#artifactory=artifactory-blr-fnms.int.net.nokia.com
HOST_BASE_PATH=/home/sdan/nav
sleep=200

if [ $AV_LABEL == "AV216" ]; then 
     avserver=10.85.185.216
elif
   [ $AV_LABEL == "AV218" ]; then 
     avserver=10.85.185.218
elif
   [ $AV_LABEL == "AV235" ]; then 
     avserver=10.85.185.235
elif
   [ $AV_LABEL == "AV237" ]; then
     avserver=10.85.185.237
elif
   [ $AV_LABEL == "AV153" ]; then 
     avserver=10.74.71.153
elif
   [ $AV_LABEL == "AV8" ]; then 
     avserver=10.85.183.8     
elif
   [ $AV_LABEL == "AV4" ]; then 
     avserver=10.85.183.4     
elif
   [ $AV_LABEL == "AV90" ]; then 
     avserver=10.131.234.90
     HOST_BASE_PATH=/root
elif
   [ $AV_LABEL == "AV253" ]; then 
     avserver=10.131.227.253
     HOST_BASE_PATH=/root
elif
   [ $AV_LABEL == "AV254" ]; then
     avserver=10.74.70.254
elif
   [ $AV_LABEL == "ANT190" ]; then
     avserver=10.164.200.190    
     HOST_BASE_PATH=/home/jshah001
     avserver_int=192.168.0.19
elif
   [ $AV_LABEL == "ANT252" ]; then
     avserver=10.157.58.252    
     HOST_BASE_PATH=/home/kajmi
     avserver_int=192.168.0.11
elif
   [ $AV_LABEL == "ANT22" ]; then
     avserver=138.203.132.22   
     HOST_BASE_PATH=/home/acuroy
     avserver_int=138.203.132.22    
elif
   [ $AV_LABEL == "ANT55" ]; then
     avserver=10.157.49.55
     HOST_BASE_PATH=/home/hamin
     avserver_int=10.157.49.55
elif
   [ $AV_LABEL == "ANT106" ]; then
     avserver=138.203.132.106  
     HOST_BASE_PATH=/home/vaesenw
     avserver_int=138.203.132.106     
elif
   [ $AV_LABEL == "ANT44" ]; then
     avserver=10.157.54.44  
     HOST_BASE_PATH=/home/vaesenw
     avserver_int=192.168.0.15
elif
   [ $AV_LABEL == "ANT118" ]; then
     avserver=10.157.54.118  
     HOST_BASE_PATH=/home/zghedira
     avserver_int=192.168.0.7	
elif
   [ $AV_LABEL == "ANT43" ]; then
     avserver=10.181.200.43  
     HOST_BASE_PATH=/home/diericli
     avserver_int=192.168.0.5		 
fi

set +e
mkdir $HOME/plugin
set -e


cd $HOST_BASE_PATH


sudo helm repo update
if [ $BUILD == "latest" ]; then
    if [ $RELEASE == "21.9.0-SNAPSHOT" ]; then
	    Latest_url=http://10.157.88.36:8080/job/Altiplano-Integration/lastStableBuild/
	elif [ $RELEASE == "21.3.2-REL" ]; then
	    Latest_url=http://10.157.88.36:8080/job/Altiplano-Integration-21.3-release/lastStableBuild/
    elif [ $RELEASE == "21.6.0-REL" ] ; then
	    Latest_url=http://10.157.88.36:8080/job/Altiplano-Integration-21.6-release/lastStableBuild/
    fi

    wget -q -O temp.html "$Latest_url" --no-proxy
    Build_num=$(cat temp.html | grep -o "Build #[0-9]*" | cut -d '#' -f 2)	
    if [ $RELEASE == "21.3.2-REL" ]; then
	Build_num=`printf "%04d\n" "$Build_num"`
	fi
    if [ $RELEASE == "21.6.0-REL" ]; then
	Build_num=`printf "%04d\n" "$Build_num"`
	fi
	Helm_tag="$RELEASE"-$Build_num	
else
    Helm_tag="$RELEASE"-"$BUILD"
    Build_num="$BUILD"
    Build_tag=""
fi

echo "$Helm_tag"
#if [ $VONU_PLUG != '' ]; then
#	BBA_tag=$VONU_PLUG
#fi


#version=`sudo helm search repo altiplano_helm_cr_virtual --devel | grep $Helm_tag | cut -f 2 |head -1 | tr -d ' '`
version=$Helm_tag
set_parameters="--set altiplano-vonuproxy.service.mgmtType=NodePort"
set_parameters_infra=$set_parameters_infra" --set altiplano-ingress.tcp.30801=default/nokia-altiplano-vonuproxy-mgmt:8801"
set_parameters=$set_parameters"  --set global.ingressReleaseName=nokia-infra"

if [ $EXTRA_PARAMS ]; then
	if [[ $EXTRA_PARAMS =~ "mobility" ]]; then
		 set_parameters=$set_parameters" --set altiplano-victproxy.service.mgmtType=NodePort --set altiplano-datasyncproxy.service.mgmtType=NodePort --set altiplano-victp.enabled=true --set altiplano-victpproxy.enabled=true --set altiplano-datasyncctlr.enabled=true --set altiplano-datasyncproxy.enabled=true --set altiplano-av.env.open.ENABLE_VICTP_FILTERING_LISTENERS=true"
    fi     
#	if
#	   [[ $EXTRA_PARAMS =~ "vonumanagement-REST-API" ]]; then 
#		 set_parameters=$set_parameters" --set altiplano-vonumanagement.service.mgmtType=NodePort"
#	fi
#	if 
#       [[ $EXTRA_PARAMS =~ "vonuproxy-GUI" ]]; then
#         set_parameters=$set_parameters" --set altiplano-vonuproxy.service.mgmtType=NodePort"
#    fi
    if
	   [[ $EXTRA_PARAMS =~ "no-TLS" ]]; then 
		 set_parameters_infra=$set_parameters_infra" --set global.use_tls=false --set altiplano-mariadb.mariadb.use_tls=false"
		 set_parameters=$set_parameters" --set global.use_tls=false"
	fi
    
    if
	   [[ $EXTRA_PARAMS =~ "vCLI" ]]; then 
		 set_parameters=$set_parameters" --set tags.topa=true"
	fi    
fi


if [ $light_version == "yes" ]; then
	set_parameters_infra=$set_parameters_infra" --set altiplano-pmfilegenerator.enabled=false --set altiplano-pts-kube-state-metrics.enabled=false --set altiplano-pts-node-exporter.enabled=false --set altiplano-pts-pushgateway.enabled=false --set altiplano-pts-server.enabled=false"
	set_parameters=$set_parameters" --set altiplano-healthengine.enabled=false --set altiplano-ipfixbecollector.enabled=false --set altiplano-ipfixfecollector.enabled=false --set altiplano-nclivecollector.enabled=false --set altiplano-netconfinventorycollector.enabled=false --set altiplano-rcdeviceproxy.enabled=false --set altiplano-tcaengine.enabled=false"	
fi


command="sudo kubectl get pods --all-namespaces"
av_pod=$($command | grep altiplano-av | grep -v Terminating | awk '{print $2}')


if [ $SKIP_UPGRADE == "no" ]; then

	set +e
	sudo helm list 2> error
	ERROR=$(cat error | awk -F':' '{print $2}' |awk '{$1=$1};1')
	#echo $ERROR
	
	if [ "$ERROR" ]; then
		#echo "error case" 
		#exit 
		sudo kubectl create serviceaccount --namespace kube-system tiller
		sudo kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
		sudo kubectl patch deploy --namespace kube-system tiller-deploy -p '{"spec":{"template":{"spec":{"serviceAccount":"tiller"}}}}'
		sudo kubectl create clusterrolebinding add-on-cluster-admin --clusterrole=cluster-admin --serviceaccount=kube-system:default
		#sudo helm init --service-account tiller --upgrade
	fi
    
    if [[ $AV_LABEL != "ANT"* ]]; then
   		USAGE=$(df -hk | grep da2 |  awk '{print $5}' | sed 's/%//g')
	    USAGE1=$(df -hk | grep mapper |  awk '{print $5}' | sed 's/%//g')
    	if  [ $USAGE -gt 70 ] || [ $USAGE1 -gt 70 ];  then
      		docker rmi $(docker images -q)
    	fi
	fi
	set -e
	
	#name=$(sudo helm list | grep DEPLOYED | awk '{print $1}')
    sudo helm list
    name=$(sudo helm list | grep -v NAME | tail -1 | awk '{print $1}')
	while [ $name ]; do
    	sudo helm uninstall --no-hooks $name
        sleep 10
        name=$(sudo helm list | grep -v NAME | tail -1 | awk '{print $1}')
    done
    
    if [ ! -e altiplano-solution-$version.tgz ]; then   	
	sudo helm pull altiplano_helm_cr_virtual/altiplano-solution --version $version
    fi
	sudo rm -rf altiplano-solution/
	sudo tar xzvf altiplano-solution-$version.tgz
    
    if [ ! -e altiplano-infra-$version.tgz ]; then   	
	sudo helm pull altiplano_helm_cr_virtual/altiplano-infra --version $version
    fi
	sudo rm -rf altiplano-infra/
	sudo tar xzvf altiplano-infra-$version.tgz
    
    if [ ! -e altiplano-secrets-$version.tgz ]; then   	
	sudo helm pull altiplano_helm_cr_virtual/altiplano-secrets --version $version
    fi
	sudo rm -rf altiplano-secrets/
	sudo tar xzvf altiplano-secrets-$version.tgz

    set +e
    sudo kubectl delete cm ingress-controller-leader-nginx
    sudo kubectl delete job nokia-infra-altiplano-redis-pre-delete
    sudo kubectl delete service nokia-infra-altiplano-redis
    sudo kubectl delete secret nokia-infra-altiplano-redis-redis-secrets
    sudo kubectl delete secret nokia-infra-altiplano-redis-admin-secrets
    sudo kubectl delete secret nokia-infra-altiplano-mariadb-mariadb-initialusers
    sudo kubectl delete secret nokia-altiplano-ac
    sudo kubectl delete roles nokia-infra-altiplano-redis-install
    sudo kubectl delete service nokia-infra-altiplano-redis-install
    sudo kubectl delete serviceaccounts nokia-infra-altiplano-redis-install
    sudo kubectl delete rolebindings nokia-infra-altiplano-redis-install
    sudo kubectl delete roles nokia-infra-altiplano-mariadb-install
    sudo kubectl delete serviceaccounts nokia-infra-altiplano-mariadb-install
    sudo kubectl delete rolebindings nokia-infra-altiplano-mariadb-install   
    sudo kubectl delete secret nokia-infra-altiplano-grafana
    sudo helm uninstall --no-hooks nokia
    sudo helm uninstall --no-hooks nokia-infra
	sudo helm uninstall --no-hooks nokia-secrets
    sudo ip link set docker0 promisc on
    set -e
    sudo helm upgrade -i nokia-secrets -f $HOST_BASE_PATH/altiplano-secrets/values.yaml $HOST_BASE_PATH/altiplano-secrets --timeout 1000s
	sleep 20
     sudo helm upgrade -i nokia-infra --set tags.premium=true --set global.registry=$artifactory:9000 --set global.registry1=$artifactory:9000 --set global.registry3=$artifactory:9000 -f $HOST_BASE_PATH/altiplano-infra/values.yaml $HOST_BASE_PATH/altiplano-infra --set global.K8S_PUBLIC_IP=$avserver --set global.persistence=false --set altiplano-mariadb.mariadb.persistence.enabled=false --set altiplano-mariadb.mariadb.persistence.backup.enabled=false $set_parameters_infra --timeout 1000s
	sleep 20
     sudo helm upgrade -i nokia --set tags.premium=true --set global.registry=$artifactory:9000 --set global.registry1=$artifactory:9000 -f $HOST_BASE_PATH/altiplano-solution/values.yaml $HOST_BASE_PATH/altiplano-solution --set global.K8S_PUBLIC_IP=$avserver --set global.persistence=false --set altiplano-av.env.open.ENABLE_VONU=true $set_parameters --timeout 1000s

    sleep 10 
	av_pod=$($command | grep altiplano-av | grep -v Terminating | awk '{print $2}')
	
    echo "Waiting for the $av_pod to get in status Running"
    while true; do
	ready=$($command | grep $av_pod | awk '{print $3}')
	status=$($command | grep $av_pod | awk '{print $4}')
	if [ $status == Running ]; then
		if [ $ready == 1/1 ]; then
        echo "$av_pod is up!"
		break
		fi
	fi  
	sleep 20
	done
    
    echo "Taking a nap, while waiting for the other pods to get up..."
	sleep $sleep
	echo AV container is up
fi



if [ $SKIP_UPGRADE == "refresh" ]; then
	sudo kubectl delete pods `sudo kubectl get pods --all-namespaces |egrep 'vonum|vonup|-av-'| awk '{print $2}'`
	sleep 60
fi

sudo kubectl get pods --all-namespaces
echo $'\nPods in status different than Running:'
sudo kubectl get pods --all-namespaces |grep -v Runn

######## Temp WA #########################################################################################
keyckloak_wa=0
    while true; do
	ready=$($command | grep keycloak | awk '{print $3}')
	restarts=$($command | grep keycloak | awk '{print $5}')
    if [ $ready == 1/1 ] || [ $restarts -ge 1 ]; then
		break
	fi  
    sleep 20
	done



ready=$($command | grep keycloak | awk '{print $3}')
restarts=$($command | grep keycloak | awk '{print $5}')
keycloak_pod=$($command | grep keycloak | grep -v Terminating | awk '{print $2}')

while true; do
if [ $ready != 1/1 ] && [ $restarts -ge 1 ]; then
    echo "keyckloak is NOT up! Trying WA solution"
    keyckloak_wa=$[$keyckloak_wa+1]
    set +e
	keycloak_pod=$($command | grep keycloak | grep -v Terminating | awk '{print $2}')
    sudo kubectl delete pod $keycloak_pod
    sleep 5
    mariadb_cid=$(sudo docker ps |grep mariadb |grep usr |awk '{print $1}')
    docker cp /home/sdan/nav/kc.sql $mariadb_cid:/import/
    sudo docker exec -i $mariadb_cid bash -c "mysql -u root -pmysql -D keycloak -e 'drop database keycloak'"
    sudo docker exec -i $mariadb_cid bash -c "mysql -u root -pmysql -e 'create database keycloak'"
    sudo docker exec -i $mariadb_cid bash -c "mysql -u root -pmysql keycloak < /import/kc.sql"
    set -e  
    sleep 60
    ready=$($command | grep keycloak | awk '{print $3}')
	restarts=$($command | grep keycloak | awk '{print $5}')
else 
	break
fi  
done

##########################################################################################################



######## SET SSH ENV for remote SSH on AV AC pods#########################################################
anv_pod=$(sudo kubectl get pods |grep nokia-altiplano-av |cut -f 1-3 -d "-")
echo "$anv_pod"
sudo kubectl set env deployment/$anv_pod NC_SSH_SERVER_DH_KEXS=diffie-hellman-group1-sha1,diffie-hellman-group14-sha1,diffie-hellman-group14-sha256,diffie-hellman-group15-sha512,diffie-hellman-group16-sha512,diffie-hellman-group17-sha512,diffie-hellman-group18-sha512,diffie-hellman-group-exchange-sha1,diffie-hellman-group-exchange-sha256,ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521
sudo kubectl set env deployment/$anv_pod NC_SSH_SERVER_CIPHERS=aes128-ctr,aes192-ctr,aes256-ctr,arcfour256,arcfour128,aes128-cbc,3des-cbc,blowfish-cbc,aes192-cbc,aes256-cbc
sudo kubectl set env deployment/$anv_pod NC_SSH_SERVER_MACS=hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha1-etm@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1,hmac-md5,hmac-sha1-96,hmac-md5-96

ac_pod=$(sudo kubectl get pods |grep nokia-altiplano-ac |cut -f 1-3 -d "-")
echo "$ac_pod"
sudo kubectl set env deployment/$ac_pod NC_SSH_SERVER_DH_KEXS=diffie-hellman-group1-sha1,diffie-hellman-group14-sha1,diffie-hellman-group14-sha256,diffie-hellman-group15-sha512,diffie-hellman-group16-sha512,diffie-hellman-group17-sha512,diffie-hellman-group18-sha512,diffie-hellman-group-exchange-sha1,diffie-hellman-group-exchange-sha256,ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521
sudo kubectl set env deployment/$ac_pod NC_SSH_SERVER_CIPHERS=aes128-ctr,aes192-ctr,aes256-ctr,arcfour256,arcfour128,aes128-cbc,3des-cbc,blowfish-cbc,aes192-cbc,aes256-cbc
sudo kubectl set env deployment/$ac_pod NC_SSH_SERVER_MACS=hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha1-etm@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1,hmac-md5,hmac-sha1-96,hmac-md5-96

sleep 100

av_pod=$($command | grep altiplano-av | grep -v Terminating | awk '{print $2}')


echo "================== Install Licesnse and update nav request timeout======================="
rel=$(echo $RELEASE | cut -d '.' -f 1)

if [ $rel == "20" ]; then

sudo echo '<config><platform:platform xmlns:platform="http://www.nokia.com/management-solutions/anv-platform"><license:license-details xmlns:license="http://www.nokia.com/management-solutions/license-management"><license:license-key xc:operation="replace" xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><license:license-name>CORE</license:license-name><license:key-string>AC8wLQIVAIWEIdT6RyaJeIaGeIrMelNKrz7yAhQx685AyBrG678eIA/WXdrC7oZe9AanrO0A
BXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVz
aG9sZHhwP0AAAAAAADB3CAAAAEAAAAAcdAAZRml4ZWRfcG9ydF9jb3VudGluZ19ydWxlc3QB
YnsicnVsZXMiOlt7ImhhcmR3YXJlLXR5cGUiOiJXUE9OLUhFQUQtQVAiLCJXUE9OIjoiMCJ9
LHsiaGFyZHdhcmUtdHlwZSI6IldQT04tUkVMQVktQVAiLCJXUE9OIjoiMCJ9LHsiaGFyZHdh
cmUtdHlwZSI6IldQT04tRVhURU5TSU9OLUFQIiwiV1BPTiI6IjAifSx7ImhhcmR3YXJlLXR5
cGUiOiJXUE9OLUhPVSIsIldQT04iOiIxIn0seyJoYXJkd2FyZS10eXBlIjoiTFMtQ0YtMjRX
IiwieERTTCI6IjAifSx7ImhhcmR3YXJlLXR5cGUiOiJMUy1GWC1GR0xULUIiLCJ4RFNMIjoi
MCJ9LHsiaGFyZHdhcmUtdHlwZSI6IkxTLUZYLUZXTFQtQiIsInhEU0wiOiIwIn0seyJoYXJk
d2FyZS10eXBlIjoiVk9OVSIsInhEU0wiOiIwIn1dfXQAC3N5c3RlbVVzYWdldAAISU5URVJO
QUx0AApPTlVDb25uZWN0dAAFZmFsc2V0AA9OZXR3b3JrX1NsaWNpbmd0AAVmYWxzZXQAD3R5
cGVCUHJvdGVjdGlvbnQABWZhbHNldAAHcmVsZWFzZXQAAjIwdAAVV1BPTl9zdWJzY3JpYmVy
X3BvcnRzdAADMTAwdAAbU05NUC1GaWJlcl9zdWJzY3JpYmVyX3BvcnRzdAABMHQAHFZhcmlh
YmxlX3BvcnRfY291bnRpbmdfcnVsZXN0AY17InJ1bGVzIjpbeyJQT1JULVRZUEUiOiJ4RFNM
X3N1YnNjcmliZXJfcG9ydHMiLCJDT1VOVC1FWFAiOiIvL2RldmljZTpkZXZpY2UvZGV2aWNl
OmRldmljZS1zcGVjaWZpYy1kYXRhL2lmOmludGVyZmFjZXMvaWY6aW50ZXJmYWNlL2JiZmZh
c3Q6bGluZS9iYmZmYXN0OmNvbmZpZ3VyZWQtbW9kZSIsIkNPVU5ULU5TIjp7ImlmIjoidXJu
OmlldGY6cGFyYW1zOnhtbDpuczp5YW5nOmlldGYtaW50ZXJmYWNlcyIsImlhbmFpZnQiOiJ1
cm46aWV0ZjpwYXJhbXM6eG1sOm5zOnlhbmc6aWFuYS1pZi10eXBlIiwiYmJmZmFzdCI6InVy
bjpiYmY6eWFuZzpiYmYtZmFzdGRzbCIsImRldmljZSI6Imh0dHA6Ly93d3cubm9raWEuY29t
L21hbmFnZW1lbnQtc29sdXRpb25zL2Fudi1kZXZpY2UtaG9sZGVycyJ9fV19dAAfRGV2aWNl
c193aXRoX3ZhcmlhYmxlX0RTTF9wb3J0c3QAOFsiU1g0RiIsIkxTLURQVS1DRkFTLU0iLCJM
Uy1EUFUtQ0ZBUy1IIiwiTFMtRFBVLUNGRVItQyJddAAVR1BPTl9zdWJzY3JpYmVyX3BvcnRz
dAADMTAwdAAGaG9zdGlkdAAEdGVzdHQAC3Byb2R1Y3ROYW1ldAAbQWx0aXBsYW5vIEFjY2Vz
cyBDb250cm9sbGVydAAQbGVnYWN5QWRhcHRlckNMSXEAfgARdAAcU05NUC1Db3BwZXJfc3Vi
c2NyaWJlcl9wb3J0c3EAfgARdAAKc3lzdGVtTmFtZXQABkFDMjAueHQAHE5HUE9OMi1UV0RN
X3N1YnNjcmliZXJfcG9ydHN0AAMxMDB0ABdHLkZhc3Rfc3Vic2NyaWJlcl9wb3J0c3QAAzEw
MHQAE01heF91bmtub3duX2RldmljZXN0AAIxMHQAFXhEU0xfc3Vic2NyaWJlcl9wb3J0c3QA
AzEwMHQADmV4cGlyYXRpb25EYXRldAAKMjAyMS8xMi8xNnQAEWxlZ2FjeUFkYXB0ZXJTT0FQ
cQB+ABF0ABdYR1NQT05fc3Vic2NyaWJlcl9wb3J0c3QAAzEwMHQADGN1c3RvbWVyTmFtZXQA
GE5PS0lBIEluZGlhICYgV2lwcm8gbGFic3QADnByb2R1Y3RWYXJpYW50dAAHUHJlbWl1bXQA
Dk5DWV9NYW5hZ2VtZW50dAAEdHJ1ZXQAEWxpY2Vuc2UuY29tcG9uZW50dAAOQWx0aXBsYW5v
IENvcmV0AAlnTW9iaWxpdHl0AAVmYWxzZXgAAA==
</license:key-string></license:license-key></license:license-details></platform:platform></config>' > core_license.xml
echo '<config><anv:device-manager xmlns:anv="http://www.nokia.com/management-solutions/anv"><adh:netconf-stack-configuration xmlns:adh="http://www.nokia.com/management-solutions/anv-device-holders"><adh:request-timeout>300</adh:request-timeout></adh:netconf-stack-configuration></anv:device-manager></config>' > modify_nav_request_timeout.xml

elif [ $rel == "21" ]; then

#NAC 21.x AAC (premium) For Slice Environment
#sudo echo '<config><platform:platform xmlns:platform="http://www.nokia.com/management-solutions/anv-platform"><license:license-details xmlns:license="http://www.nokia.com/management-solutions/license-management"><license:license-key xc:operation="replace" xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><license:license-name>CORE</license:license-name><license:key-string>AC4wLAIUQzMkLpKgXD9H2cVMsIeUFV486DkCFDBjaWEHhF3KVbAPH94LVSli7QltBaus7QAF
#c3IAEWphdmEudXRpbC5IYXNoTWFwBQfawcMWYNEDAAJGAApsb2FkRmFjdG9ySQAJdGhyZXNo
#b2xkeHA/QAAAAAAAMHcIAAAAQAAAABl0ABlGaXhlZF9wb3J0X2NvdW50aW5nX3J1bGVzdACw
#eyJydWxlcyI6W3siaGFyZHdhcmUtdHlwZSI6IkxTLUNGLTI0VyIsInhEU0wiOiIwIn0seyJo
#YXJkd2FyZS10eXBlIjoiTFMtRlgtRkdMVC1CIiwieERTTCI6IjAifSx7ImhhcmR3YXJlLXR5
#cGUiOiJMUy1GWC1GV0xULUIiLCJ4RFNMIjoiMCJ9LHsiaGFyZHdhcmUtdHlwZSI6IlZPTlUi
#LCJ4RFNMIjoiMCJ9XX10AAtzeXN0ZW1Vc2FnZXQACElOVEVSTkFMdAAKT05VQ29ubmVjdHQA
#BWZhbHNldAAPTmV0d29ya19TbGljaW5ndAAEdHJ1ZXQAD3R5cGVCUHJvdGVjdGlvbnQABWZh
#bHNldAAHcmVsZWFzZXQAAjIxdAAbU05NUC1GaWJlcl9zdWJzY3JpYmVyX3BvcnRzdAABMHQA
#HFZhcmlhYmxlX3BvcnRfY291bnRpbmdfcnVsZXN0AY17InJ1bGVzIjpbeyJQT1JULVRZUEUi
#OiJ4RFNMX3N1YnNjcmliZXJfcG9ydHMiLCJDT1VOVC1FWFAiOiIvL2RldmljZTpkZXZpY2Uv
#ZGV2aWNlOmRldmljZS1zcGVjaWZpYy1kYXRhL2lmOmludGVyZmFjZXMvaWY6aW50ZXJmYWNl
#L2JiZmZhc3Q6bGluZS9iYmZmYXN0OmNvbmZpZ3VyZWQtbW9kZSIsIkNPVU5ULU5TIjp7Imlm
#IjoidXJuOmlldGY6cGFyYW1zOnhtbDpuczp5YW5nOmlldGYtaW50ZXJmYWNlcyIsImlhbmFp
#ZnQiOiJ1cm46aWV0ZjpwYXJhbXM6eG1sOm5zOnlhbmc6aWFuYS1pZi10eXBlIiwiYmJmZmFz
#dCI6InVybjpiYmY6eWFuZzpiYmYtZmFzdGRzbCIsImRldmljZSI6Imh0dHA6Ly93d3cubm9r
#aWEuY29tL21hbmFnZW1lbnQtc29sdXRpb25zL2Fudi1kZXZpY2UtaG9sZGVycyJ9fV19dAAf
#RGV2aWNlc193aXRoX3ZhcmlhYmxlX0RTTF9wb3J0c3QAOFsiU1g0RiIsIkxTLURQVS1DRkFT
#LU0iLCJMUy1EUFUtQ0ZBUy1IIiwiTFMtRFBVLUNGRVItQyJddAAVR1BPTl9zdWJzY3JpYmVy
#X3BvcnRzdAADMTAwdAAGaG9zdGlkdAAEdGVzdHQAC3Byb2R1Y3ROYW1ldAAbQWx0aXBsYW5v
#IEFjY2VzcyBDb250cm9sbGVydAAcU05NUC1Db3BwZXJfc3Vic2NyaWJlcl9wb3J0c3EAfgAP
#dAAKc3lzdGVtTmFtZXQABkFDMjEueHQAHE5HUE9OMi1UV0RNX3N1YnNjcmliZXJfcG9ydHN0
#AAMxMDB0ABdHLkZhc3Rfc3Vic2NyaWJlcl9wb3J0c3QAAzEwMHQAE01heF91bmtub3duX2Rl
#dmljZXN0AAIxMHQAFXhEU0xfc3Vic2NyaWJlcl9wb3J0c3QAAzEwMHQADmV4cGlyYXRpb25E
#YXRldAAKMjAyMi8wMS8xNnQAF1hHU1BPTl9zdWJzY3JpYmVyX3BvcnRzdAADMTAwdAAMY3Vz
#dG9tZXJOYW1ldAAiTk9LSUEgU0RBTiBhbmQgQ09OVFJPTExFUiBBUFBTIFImRHQADnByb2R1
#Y3RWYXJpYW50dAADQUFDdAAOTkNZX01hbmFnZW1lbnR0AAR0cnVldAARbGljZW5zZS5jb21w
#b25lbnR0AA5BbHRpcGxhbm8gQ29yZXQACWdNb2JpbGl0eXQABWZhbHNleAAA
#</license:key-string></license:license-key></license:license-details></platform:platform></config>' > core_license.xml
#echo '<config><anv:device-manager xmlns:anv="http://www.nokia.com/management-solutions/anv"><adh:netconf-stack-configuration xmlns:adh="http://www.nokia.com/management-solutions/anv-device-holders"><adh:request-timeout>300</adh:request-timeout></adh:netconf-stack-configuration></anv:device-manager></config>' > modify_nav_request_timeout.xml

#NAC 21.x AAC (premium) For Non-slice Environment
sudo echo '<config><platform:platform xmlns:platform="http://www.nokia.com/management-solutions/anv-platform"><license:license-details xmlns:license="http://www.nokia.com/management-solutions/license-management"><license:license-key xc:operation="replace" xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><license:license-name>CORE</license:license-name><license:key-string>ADAwLgIVAJOFZuuRM0lsorx26xJ5qfhVnuxjAhUAghU0GBexJKir1LmFuqtc9zHnq5cFrKzt
AAVzcgARamF2YS51dGlsLkhhc2hNYXAFB9rBwxZg0QMAAkYACmxvYWRGYWN0b3JJAAl0aHJl
c2hvbGR4cD9AAAAAAAAwdwgAAABAAAAAGXQAGUZpeGVkX3BvcnRfY291bnRpbmdfcnVsZXN0
ALB7InJ1bGVzIjpbeyJoYXJkd2FyZS10eXBlIjoiTFMtQ0YtMjRXIiwieERTTCI6IjAifSx7
ImhhcmR3YXJlLXR5cGUiOiJMUy1GWC1GR0xULUIiLCJ4RFNMIjoiMCJ9LHsiaGFyZHdhcmUt
dHlwZSI6IkxTLUZYLUZXTFQtQiIsInhEU0wiOiIwIn0seyJoYXJkd2FyZS10eXBlIjoiVk9O
VSIsInhEU0wiOiIwIn1dfXQAC3N5c3RlbVVzYWdldAAISU5URVJOQUx0AApPTlVDb25uZWN0
dAAFZmFsc2V0AA9OZXR3b3JrX1NsaWNpbmd0AAVmYWxzZXQAD3R5cGVCUHJvdGVjdGlvbnQA
BWZhbHNldAAHcmVsZWFzZXQAAjIxdAAbU05NUC1GaWJlcl9zdWJzY3JpYmVyX3BvcnRzdAAB
MHQAHFZhcmlhYmxlX3BvcnRfY291bnRpbmdfcnVsZXN0AY17InJ1bGVzIjpbeyJQT1JULVRZ
UEUiOiJ4RFNMX3N1YnNjcmliZXJfcG9ydHMiLCJDT1VOVC1FWFAiOiIvL2RldmljZTpkZXZp
Y2UvZGV2aWNlOmRldmljZS1zcGVjaWZpYy1kYXRhL2lmOmludGVyZmFjZXMvaWY6aW50ZXJm
YWNlL2JiZmZhc3Q6bGluZS9iYmZmYXN0OmNvbmZpZ3VyZWQtbW9kZSIsIkNPVU5ULU5TIjp7
ImlmIjoidXJuOmlldGY6cGFyYW1zOnhtbDpuczp5YW5nOmlldGYtaW50ZXJmYWNlcyIsImlh
bmFpZnQiOiJ1cm46aWV0ZjpwYXJhbXM6eG1sOm5zOnlhbmc6aWFuYS1pZi10eXBlIiwiYmJm
ZmFzdCI6InVybjpiYmY6eWFuZzpiYmYtZmFzdGRzbCIsImRldmljZSI6Imh0dHA6Ly93d3cu
bm9raWEuY29tL21hbmFnZW1lbnQtc29sdXRpb25zL2Fudi1kZXZpY2UtaG9sZGVycyJ9fV19
dAAfRGV2aWNlc193aXRoX3ZhcmlhYmxlX0RTTF9wb3J0c3QAOFsiU1g0RiIsIkxTLURQVS1D
RkFTLU0iLCJMUy1EUFUtQ0ZBUy1IIiwiTFMtRFBVLUNGRVItQyJddAAVR1BPTl9zdWJzY3Jp
YmVyX3BvcnRzdAADMTAwdAAGaG9zdGlkdAAEdGVzdHQAC3Byb2R1Y3ROYW1ldAAbQWx0aXBs
YW5vIEFjY2VzcyBDb250cm9sbGVydAAcU05NUC1Db3BwZXJfc3Vic2NyaWJlcl9wb3J0c3EA
fgAPdAAKc3lzdGVtTmFtZXQABkFDMjEueHQAHE5HUE9OMi1UV0RNX3N1YnNjcmliZXJfcG9y
dHN0AAMxMDB0ABdHLkZhc3Rfc3Vic2NyaWJlcl9wb3J0c3QAAzEwMHQAE01heF91bmtub3du
X2RldmljZXN0AAIxMHQAFXhEU0xfc3Vic2NyaWJlcl9wb3J0c3QAAzEwMHQADmV4cGlyYXRp
b25EYXRldAAKMjAyMi8wMS8xNnQAF1hHU1BPTl9zdWJzY3JpYmVyX3BvcnRzdAADMTAwdAAM
Y3VzdG9tZXJOYW1ldAAiTk9LSUEgU0RBTiBhbmQgQ09OVFJPTExFUiBBUFBTIFImRHQADnBy
b2R1Y3RWYXJpYW50dAADQUFDdAAOTkNZX01hbmFnZW1lbnR0AAR0cnVldAARbGljZW5zZS5j
b21wb25lbnR0AA5BbHRpcGxhbm8gQ29yZXQACWdNb2JpbGl0eXQABWZhbHNleAAA
</license:key-string></license:license-key></license:license-details></platform:platform></config>' > core_license.xml
echo '<config><anv:device-manager xmlns:anv="http://www.nokia.com/management-solutions/anv"><adh:netconf-stack-configuration xmlns:adh="http://www.nokia.com/management-solutions/anv-device-holders"><adh:request-timeout>300</adh:request-timeout></adh:netconf-stack-configuration></anv:device-manager></config>' > modify_nav_request_timeout.xml


else

sudo echo '<config><platform:platform xmlns:platform="http://www.nokia.com/management-solutions/anv-platform"><license:license-details xmlns:license="http://www.nokia.com/management-solutions/license-management"><license:license-key xc:operation="replace" xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><license:license-name>CORE</license:license-name><license:key-string>AC8wLQIVAIWEIdT6RyaJeIaGeIrMelNKrz7yAhQx685AyBrG678eIA/WXdrC7oZe9AanrO0A
BXNyABFqYXZhLnV0aWwuSGFzaE1hcAUH2sHDFmDRAwACRgAKbG9hZEZhY3RvckkACXRocmVz
aG9sZHhwP0AAAAAAADB3CAAAAEAAAAAcdAAZRml4ZWRfcG9ydF9jb3VudGluZ19ydWxlc3QB
YnsicnVsZXMiOlt7ImhhcmR3YXJlLXR5cGUiOiJXUE9OLUhFQUQtQVAiLCJXUE9OIjoiMCJ9
LHsiaGFyZHdhcmUtdHlwZSI6IldQT04tUkVMQVktQVAiLCJXUE9OIjoiMCJ9LHsiaGFyZHdh
cmUtdHlwZSI6IldQT04tRVhURU5TSU9OLUFQIiwiV1BPTiI6IjAifSx7ImhhcmR3YXJlLXR5
cGUiOiJXUE9OLUhPVSIsIldQT04iOiIxIn0seyJoYXJkd2FyZS10eXBlIjoiTFMtQ0YtMjRX
IiwieERTTCI6IjAifSx7ImhhcmR3YXJlLXR5cGUiOiJMUy1GWC1GR0xULUIiLCJ4RFNMIjoi
MCJ9LHsiaGFyZHdhcmUtdHlwZSI6IkxTLUZYLUZXTFQtQiIsInhEU0wiOiIwIn0seyJoYXJk
d2FyZS10eXBlIjoiVk9OVSIsInhEU0wiOiIwIn1dfXQAC3N5c3RlbVVzYWdldAAISU5URVJO
QUx0AApPTlVDb25uZWN0dAAFZmFsc2V0AA9OZXR3b3JrX1NsaWNpbmd0AAVmYWxzZXQAD3R5
cGVCUHJvdGVjdGlvbnQABWZhbHNldAAHcmVsZWFzZXQAAjIwdAAVV1BPTl9zdWJzY3JpYmVy
X3BvcnRzdAADMTAwdAAbU05NUC1GaWJlcl9zdWJzY3JpYmVyX3BvcnRzdAABMHQAHFZhcmlh
YmxlX3BvcnRfY291bnRpbmdfcnVsZXN0AY17InJ1bGVzIjpbeyJQT1JULVRZUEUiOiJ4RFNM
X3N1YnNjcmliZXJfcG9ydHMiLCJDT1VOVC1FWFAiOiIvL2RldmljZTpkZXZpY2UvZGV2aWNl
OmRldmljZS1zcGVjaWZpYy1kYXRhL2lmOmludGVyZmFjZXMvaWY6aW50ZXJmYWNlL2JiZmZh
c3Q6bGluZS9iYmZmYXN0OmNvbmZpZ3VyZWQtbW9kZSIsIkNPVU5ULU5TIjp7ImlmIjoidXJu
OmlldGY6cGFyYW1zOnhtbDpuczp5YW5nOmlldGYtaW50ZXJmYWNlcyIsImlhbmFpZnQiOiJ1
cm46aWV0ZjpwYXJhbXM6eG1sOm5zOnlhbmc6aWFuYS1pZi10eXBlIiwiYmJmZmFzdCI6InVy
bjpiYmY6eWFuZzpiYmYtZmFzdGRzbCIsImRldmljZSI6Imh0dHA6Ly93d3cubm9raWEuY29t
L21hbmFnZW1lbnQtc29sdXRpb25zL2Fudi1kZXZpY2UtaG9sZGVycyJ9fV19dAAfRGV2aWNl
c193aXRoX3ZhcmlhYmxlX0RTTF9wb3J0c3QAOFsiU1g0RiIsIkxTLURQVS1DRkFTLU0iLCJM
Uy1EUFUtQ0ZBUy1IIiwiTFMtRFBVLUNGRVItQyJddAAVR1BPTl9zdWJzY3JpYmVyX3BvcnRz
dAADMTAwdAAGaG9zdGlkdAAEdGVzdHQAC3Byb2R1Y3ROYW1ldAAbQWx0aXBsYW5vIEFjY2Vz
cyBDb250cm9sbGVydAAQbGVnYWN5QWRhcHRlckNMSXEAfgARdAAcU05NUC1Db3BwZXJfc3Vi
c2NyaWJlcl9wb3J0c3EAfgARdAAKc3lzdGVtTmFtZXQABkFDMjAueHQAHE5HUE9OMi1UV0RN
X3N1YnNjcmliZXJfcG9ydHN0AAMxMDB0ABdHLkZhc3Rfc3Vic2NyaWJlcl9wb3J0c3QAAzEw
MHQAE01heF91bmtub3duX2RldmljZXN0AAIxMHQAFXhEU0xfc3Vic2NyaWJlcl9wb3J0c3QA
AzEwMHQADmV4cGlyYXRpb25EYXRldAAKMjAyMS8xMi8xNnQAEWxlZ2FjeUFkYXB0ZXJTT0FQ
cQB+ABF0ABdYR1NQT05fc3Vic2NyaWJlcl9wb3J0c3QAAzEwMHQADGN1c3RvbWVyTmFtZXQA
GE5PS0lBIEluZGlhICYgV2lwcm8gbGFic3QADnByb2R1Y3RWYXJpYW50dAAHUHJlbWl1bXQA
Dk5DWV9NYW5hZ2VtZW50dAAEdHJ1ZXQAEWxpY2Vuc2UuY29tcG9uZW50dAAOQWx0aXBsYW5v
IENvcmV0AAlnTW9iaWxpdHl0AAVmYWxzZXgAAA==
</license:key-string></license:license-key></license:license-details></platform:platform></config>' > core_license.xml
sudo echo '<config><anv:device-manager xmlns:anv="http://www.nokia.com/management-solutions/anv"><adh:netconf-stack-configuration xmlns:adh="http://www.nokia.com/management-solutions/anv-device-holders"><adh:request-timeout>300</adh:request-timeout></adh:netconf-stack-configuration></anv:device-manager></config>' > modify_nav_request_timeout.xml

fi

if [[ $AV_LABEL == "ANT"* ]]; then
	avserver_ext=$avserver
	avserver=$avserver_int
fi

timeout=0
until [ $timeout -ge 40 ]; do
  sudo python edit_config_k8s.py core_license.xml $avserver -s && break 
  timeout=$[$timeout+1]
  sleep 20
done


if [ "$timeout" == "40" ]; then
   sudo python edit_config_k8s.py core_license.xml $avserver -s
fi



timeout=0
until [ $timeout -ge 20 ]; do
  sudo python edit_config_k8s.py modify_nav_request_timeout.xml $avserver -s  && break
  timeout=$[$timeout+1]
  sleep 10
done


if [ "$timeout" == "20" ]; then
    sudo python edit_config_k8s.py modify_nav_request_timeout.xml $avserver -s 
fi

set +e

timeout=0
until [ $timeout -ge 40 ]; do
  sudo python edit_config_k8s_ac.py core_license.xml $avserver -s  && break
  timeout=$[$timeout+1]
  sleep 10
done

if [ "$timeout" == "40" ]; then
  sudo python edit_config_k8s_ac.py core_license.xml $avserver -s 
fi

sleep 10

echo "================== RPC to connect AV and AC ======================="

#if [[ $AV_LABEL == "ANT"* ]]; then
#	avserver_ext=$avserver
#	avserver=$avserver_int
#fi

if [ $SKIP_UPGRADE == "no" ]; then
  echo '<config> <mds:manager-directory xmlns:mds="http://www.nokia.com/management-solutions/manager-directory-service"> <mds:manager-info xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xc:operation="create">' > AV_AC_connect.xml 
else
  echo '<config> <mds:manager-directory xmlns:mds="http://www.nokia.com/management-solutions/manager-directory-service"> <mds:manager-info xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xc:operation="replace">' > AV_AC_connect.xml 
fi
echo "<mds:name>Altiplano_AV</mds:name> <mds:ip>$avserver</mds:ip> <mds:netconf-port>6514</mds:netconf-port> <mds:protocol>https</mds:protocol> <mds:manager-type>NAV</mds:manager-type> <mds:user-name>adminuser</mds:user-name> <mds:password>password</mds:password> <mds:max-connections>5</mds:max-connections> <mds:http-url>https://$avserver/nokia-altiplano-av</mds:http-url> <mds:vonumgmt-address>tcp://$avserver:30802/</mds:vonumgmt-address> </mds:manager-info> </mds:manager-directory> </config>" >> AV_AC_connect.xml
  

timeout=0
until [ $timeout -ge 20 ]; do
  sudo python edit_config_k8s_ac.py AV_AC_connect.xml $avserver -s  && break
  timeout=$[$timeout+1]
  sleep 10
done

if [ "$timeout" == "20" ]; then
  sudo python edit_config_k8s_ac.py AV_AC_connect.xml $avserver -s 
fi



sleep 10

echo "================== RPC to create extra link app in AC QUI ======================="
vproxymgmt_port=`sudo kubectl get svc|grep vonuproxy-mgmt | awk '{print $(NF-1)}' | cut -d ':' -f 2 | cut -d '/' -f 1`
echo ' <config><platform:platform xmlns:platform="http://www.nokia.com/management-solutions/anv-platform"><app:external-application xmlns:app="http://www.nokia.com/management-solutions/external-application"> ' > AC_more_app.xml 
if
   [[ $EXTRA_PARAMS =~ "vonuproxy-GUI" ]]; then
		echo "<app:web-application ><app:name>Vproxy</app:name><app:description>Vonuproxy Web UI</app:description><app:short-name>VP</app:short-name><app:url>http://$avserver:$vproxymgmt_port/web/vonuproxy.html</app:url></app:web-application><app:web-application ><app:name>Kibana</app:name><app:description>View the logs of containers and node syslog</app:description><app:short-name>KB</app:short-name><app:url>https://$avserver/altiplano-kibana</app:url></app:web-application><app:web-application ><app:name>Virtualizer</app:name><app:description>Network virtualizer</app:description><app:short-name>AV</app:short-name><app:url>https://$avserver/nokia-altiplano-av</app:url></app:web-application></app:external-application></platform:platform></config> " >> AC_more_app.xml
else
		echo "<app:web-application ><app:name>Kibana</app:name><app:description>View the logs of containers and node syslog</app:description><app:short-name>KB</app:short-name><app:url>https://$avserver/altiplano-kibana</app:url></app:web-application><app:web-application ><app:name>Virtualizer</app:name><app:description>Network virtualizer</app:description><app:short-name>AV</app:short-name><app:url>https://$avserver/nokia-altiplano-av</app:url></app:web-application></app:external-application></platform:platform></config> " >> AC_more_app.xml
fi        


timeout=0
until [ $timeout -ge 20 ]; do
  sudo python edit_config_k8s_ac.py AC_more_app.xml $avserver -s  && break
  timeout=$[$timeout+1]
  sleep 10
done

if [ "$timeout" == "20" ]; then
  sudo python edit_config_k8s_ac.py AC_more_app.xml $avserver -s 
fi


sleep 10

set -e


echo "==================Download extra tar file for device extensions ======================="#
rel=$(echo $LT_RELEASE | cut -d '.' -f 1,2 | tr -d '.')
year1=$(echo $RELEASE | cut -d '.' -f 1)
month1=$(echo $RELEASE | cut -d '.' -f 2)
year2=$(echo $LT_RELEASE | cut -d '.' -f 1)
month2=$(echo $LT_RELEASE | cut -d '.' -f 2 | sed 's/0//')

    
MINIOLT_extension="device-extension_LS-DF-CFXR-A_$year2."$month2"_$LT_EXTENSION.zip"
FGLTB_extension="device-extension_LS-FX-FGLT-B_$year2."$month2"_$LT_EXTENSION.zip"
FWLTB_extension="device-extension_LS-FX-FWLT-B_$year2."$month2"_$LT_EXTENSION.zip"
MF2_LWLTC_extension="device-extension_LS-MF-LWLT-C_$year2."$month2"_$LT_EXTENSION.zip"
MF2_LMNTA_extension="device-extension_LS-MF-LMNT-A_$year2."$month2"_$LT_EXTENSION.zip"
NT_FX8_extension="device-extension_LS-FX-FANT-F-FX8_$year2."$month2"_$NT_FX8.zip"
NT_FX16_extension="device-extension_LS-FX-FANT-F-FX16_$year2."$month2"_$NT_FX16.zip"
NT_FX4_extension="device-extension_LS-FX-FANT-F-FX4_$year2."$month2"_$NT_FX4.zip"

extra_file=lightspan_"$rel"."$LT_EXTENSION".extra.tar
cd $HOST_BASE_PATH
if [ -e $HOST_BASE_PATH/$extra_file ]; then
	echo "extra file exists"
else
	if [[ $AV_LABEL == "ANT"* ]]; then
		wget http://aww.dsl.alcatel.be/ftp/pub/outgoing/ESAM/DAILY/packageme_"$rel"."$LT_EXTENSION"/$extra_file
    else    
    	scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null sdan@10.85.185.172:/home/sdan/builds/$extra_file $HOST_BASE_PATH
    fi
fi
sudo rm -rf $HOST_BASE_PATH/internal
sudo tar xvf $extra_file
device_ext_path=$HOST_BASE_PATH/internal/YANG


echo "================== Install Sdvonu plug $vonu_plugin ======================="
#if [ $BUILD != "latest" ]; then
#	anv_ps=`sudo docker ps | grep anv | grep -v Terminating | awk '{print $1}'`
#	Build_tag=`sudo docker logs $anv_ps | grep -o "anv-"$RELEASE"_"[0-9]* | cut -d '_' -f 2` 
#if [ $RELEASE == "21.3.2-REL" ]; then
#	RELEASE=21.3.2-REL
#fi
	if  [ "$VONU_PLUG" == '' ]; then
		BBA_tag=$(cat $HOST_BASE_PATH/altiplano-solution/values.yaml | grep '^altiplano-vonuproxy' -A 5 | grep tag | tr -d 'tag: ' | cut -d '_' -f 2 | tr -dc '0-9')
    else
       BBA_tag=$VONU_PLUG
    fi
#fi
vonu_plugin="$RELEASE"_"$BBA_tag"	

#vonu_plugin_url=http://$artifactory/artifactory/libs_cr_local/com/nokia/anv/plug/vonu/$year1/$month1/device-extensions/device-extension-vonu-$year1.$month1-1/$vonu_plugin/device-extension-vonu-$year1.$month1-1-$vonu_plugin.zip
vonu_plugin_url=http://10.131.69.114:8081/artifactory/libs_cr_local/com/nokia/anv/plug/vonu/$year1/$month1/device-extensions/device-extension-vonu-$year1.$month1-1/$vonu_plugin/device-extension-vonu-$year1.$month1-1-$vonu_plugin.zip
   
if [ -e $HOST_BASE_PATH/device-extension-vonu-$year1.$month1-1-$vonu_plugin.zip ]; then
    echo "Sdvonu plug exists"
else
    sudo wget  $vonu_plugin_url  --no-proxy
fi
sudo kubectl cp device-extension-vonu-$year1.$month1-1-$vonu_plugin.zip $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > sdvonu_plug.xml
sudo echo "<definition-archive>device-extension-vonu-"$year1"."$month1"-1-"$vonu_plugin".zip</definition-archive></deploy-device-plug>" >> sdvonu_plug.xml
sudo python add_plug_k8s.py sdvonu_plug.xml $avserver -s
sleep 20

echo "================== Install Sdfx fglt-b plug $FGLTB_extension ======================="
sudo kubectl cp $device_ext_path/$FGLTB_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > fgltb_plug.xml
sudo echo "<definition-archive>$FGLTB_extension</definition-archive></deploy-device-plug>" >> fgltb_plug.xml
sudo python  add_plug_k8s.py fgltb_plug.xml $avserver -s	
sleep 15

echo "==================Install Sdfx fwlt-b plug $FWLTB_extension ======================="
sudo kubectl cp $device_ext_path/$FWLTB_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > fwltb_plug.xml
sudo echo "<definition-archive>$FWLTB_extension</definition-archive></deploy-device-plug>" >> fwltb_plug.xml
sudo python  add_plug_k8s.py fwltb_plug.xml $avserver -s	
sleep 15

echo "==================Install mf-2 lmnt-a plug $MF2_LMNTA_extension ======================="
sudo kubectl cp $device_ext_path/$MF2_LMNTA_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > mf2_lmnta_plug.xml
sudo echo "<definition-archive>$MF2_LMNTA_extension</definition-archive></deploy-device-plug>" >> mf2_lmnta_plug.xml
sudo python  add_plug_k8s.py mf2_lmnta_plug.xml $avserver -s	
sleep 15

echo "==================Install mf-2 lwlt-c plug $MF2_LWLTC_extension ======================="
sudo kubectl cp $device_ext_path/$MF2_LWLTC_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > mf2_lwltc_plug.xml
sudo echo "<definition-archive>$MF2_LWLTC_extension</definition-archive></deploy-device-plug>" >> mf2_lwltc_plug.xml
sudo python  add_plug_k8s.py mf2_lwltc_plug.xml $avserver -s	
sleep 15

echo "==================Install MINIOLT plug $MINIOLT_extension ======================="#
sudo kubectl cp $device_ext_path/$MINIOLT_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > miniolt_plug.xml
sudo echo "<definition-archive>$MINIOLT_extension</definition-archive></deploy-device-plug>" >> miniolt_plug.xml
sudo python  add_plug_k8s.py miniolt_plug.xml $avserver -s	
sleep 15

extra_file_NT4=lightspan_"$rel"."$NT_FX4".extra.tar
extra_file_NT8=lightspan_"$rel"."$NT_FX8".extra.tar
extra_file_NT16=lightspan_"$rel"."$NT_FX16".extra.tar

if [ "$extra_file_NT16" != "$extra_file" ] ; then
	if [ -e $HOST_BASE_PATH/$extra_file_NT16 ]; then
		echo "NT16 extra file exists"
	else
		if [[ $AV_LABEL == "ANT"* ]]; then
			wget http://aww.dsl.alcatel.be/ftp/pub/outgoing/ESAM/DAILY/packageme_"$rel"."$NT_FX16"/$extra_file_NT16
		else  	
			scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null sdan@10.85.185.172:/home/sdan/builds/$extra_file_NT16 $HOST_BASE_PATH	
		fi
	fi
	sudo rm -rf $HOST_BASE_PATH/internal
	sudo tar xvf $extra_file_NT16
fi
echo "==================Install NT-FX16 plug $NT_FX16_extension ======================="#
sudo kubectl cp $device_ext_path/$NT_FX16_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > ntfx16_plug.xml
sudo echo "<definition-archive>$NT_FX16_extension</definition-archive></deploy-device-plug>" >> ntfx16_plug.xml
sudo python  add_plug_k8s.py ntfx16_plug.xml $avserver -s	
sleep 15

if [ "$extra_file_NT8" != "$extra_file_NT16" ] ; then
	if [ -e $HOST_BASE_PATH/$extra_file_NT8 ]; then
		echo "NT8 extra file exists"
	else
		if [[ $AV_LABEL == "ANT"* ]]; then
			wget http://aww.dsl.alcatel.be/ftp/pub/outgoing/ESAM/DAILY/packageme_"$rel"."$NT_FX8"/$extra_file_NT8
		else 	
			scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null sdan@10.85.185.172:/home/sdan/builds/$extra_file_NT8 $HOST_BASE_PATH
		fi
	fi
	sudo rm -rf $HOST_BASE_PATH/internal
	sudo tar xvf $extra_file_NT8	
fi
echo "==================Install NT-FX8 plug $NT_FX8_extension ======================="#
sudo kubectl cp $device_ext_path/$NT_FX8_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > ntfx8_plug.xml
sudo echo "<definition-archive>$NT_FX8_extension</definition-archive></deploy-device-plug>" >> ntfx8_plug.xml
sudo python  add_plug_k8s.py ntfx8_plug.xml $avserver -s	
sleep 15

if [ "$extra_file_NT4" != "$extra_file_NT8" ] ; then
	if [ -e $HOST_BASE_PATH/$extra_file_NT4 ]; then
		echo "NT4 extra file exists"
	else
		if [[ $AV_LABEL == "ANT"* ]]; then
			wget http://aww.dsl.alcatel.be/ftp/pub/outgoing/ESAM/DAILY/packageme_"$rel"."$NT_FX4"/$extra_file_NT4
		else 	
			scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null sdan@10.85.185.172:/home/sdan/builds/$extra_file_NT4 $HOST_BASE_PATH
		fi
	fi
	sudo rm -rf $HOST_BASE_PATH/internal
	sudo tar xvf $extra_file_NT4		
fi
echo "==================Install NT-FX4 plug $NT_FX4_extension ======================="#
sudo kubectl cp $device_ext_path/$NT_FX4_extension $av_pod:/root
sudo echo '<deploy-device-plug xmlns="http://www.nokia.com/management-solutions/anv-device-plugs">' > ntfx4_plug.xml
sudo echo "<definition-archive>$NT_FX4_extension</definition-archive></deploy-device-plug>" >> ntfx4_plug.xml
sudo python  add_plug_k8s.py ntfx4_plug.xml $avserver -s	
sleep 15

if [[ $AV_LABEL == "ANT"* ]]; then
	avserver=$avserver_ext
fi

set +e

############AV 218 Temporary WA##############
#if [ $avserver == "10.85.185.218" ] && [ $SKIP_UPGRADE == "no" ]; then
#    restart=$(echo $command | docker stop $(docker ps -a -q))
#    sleep 800
#fi
##############################################

############AV 216 Temporary WA##############
#if [ $avserver == "10.85.185.216" ] && [ $SKIP_UPGRADE == "no" ]; then
#    restart=$(echo $command | docker stop $(docker ps -a -q))
#    sleep 800
#fi
##############################################

############AV 235 Temporary WA##############
#if [ $avserver == "10.85.185.235" ] && [ $SKIP_UPGRADE == "no" ]; then
#    restart=$(echo $command | docker stop $(docker ps -a -q))
#    sleep 800
#fi
##############################################


##########################################################################################################
sudo kubectl get pods --all-namespaces |grep '0\/'
nokpods=`sudo kubectl get pods --all-namespaces |grep '0\/' | grep -v 'pts-server' |wc -l`
if [ $nokpods -ge 1 ]; then 
	  echo "Restarting NOK pods..."
      sudo kubectl delete pods `sudo kubectl get pods --all-namespaces |grep '0\/'| grep -v 'pts-server' | awk '{print $2}'`
      sleep 60
fi
##########################################################################################################


echo $'\n'
sudo kubectl get pods --all-namespaces |egrep 'STATUS|0\/'
sudo kubectl get pods --all-namespaces |grep -v Runn
echo $'\n'
echo "Login: http://$avserver/nokia-altiplano-av"

set -e


echo LT_EXT='LT extension '$LT_EXTENSION >> $WORKSPACE/buildinfo
echo FULLRELEASE=$Helm_tag >> $WORKSPACE/buildinfo
echo ALNUM='vonu '$BBA_tag >> $WORKSPACE/buildinfo