# syntax=docker/dockerfile:1


FROM alpine:3.20.3

WORKDIR /opt/local/jenkins

RUN apk update \ 
    && apk add --no-cache openjdk21-jre \ 
		&& apk add --no-cache ttf-dejavu \ 
		&& apk add --no-cache bash  

RUN addgroup -S -g 102 jenkins \ 
    && adduser -S -D -s /sbin/nologin \ 
    -h /opt/local/jenkins \ 
    -u 102 jenkins -G jenkins 

RUN mkdir /home/jenkins
RUN chown jenkins:jenkins /home/jenkins/
RUN chmod g+s /home/jenkins/

USER jenkins

COPY ./jenkins.war /opt/local/jenkins/

ENV JENKINS_HOME=/home/jenkins

EXPOSE 8080
CMD ["java", "-jar", "jenkins.war"] 

