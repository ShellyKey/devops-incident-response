# devops-incident-response
Event Driven Incident Response System - Kubernetes &amp; Prometheus


# Event Driven Auto Remediation System

## 📘 Project Overview
This project implements an automated incident response system for Kubernetes using event-driven architecture. The system monitors applications, detects failures, and performs auto-remediation without human intervention.

## 🎯 Objectives
- Real-time monitoring of Kubernetes workloads  
- Automated detection of failures  
- Self-healing through remediation engine  
- Reduce manual DevOps effort  

## 🧱 Architecture
Prometheus → Alertmanager → Webhook → Remediation Engine → Kubernetes Action

## 🛠 Technologies
- Kubernetes (Minikube)
- Prometheus & Alertmanager
- Python Flask
- Docker
- kubectl

## 👥 Team Roles
- Member 1: Application & Kubernetes
- Member 2: Monitoring
- Member 3: Alerts & Automation

## 📂 Structure
- sample-app/ → demo application  
- monitoring/ → prometheus configs  
- webhook/ → alert receiver  

## 🚀 How to Run
1. Start Minikube  
2. Deploy sample app  
3. Install Prometheus  
4. Configure alerts  

## 📌 Future Scope
- Email/SMS notifications  
- AI based decision engine  
- Multi cluster support  
