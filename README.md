# Devops-Incident-Response
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
<img width="428" height="336" alt="image" src="https://github.com/user-attachments/assets/bf3e800d-7e72-416f-ac4d-4d3bf4dc168f" />


## 🛠 Technologies
- Kubernetes (Minikube)
- Prometheus & Alertmanager
- Python Flask
- Docker
- kubectl

## 👥 Team Roles
Member 1: Prometheus & Grafana Setup
Member 2: Alert Rules Configuration
Member 3: Remediation Scripts & GitHub

## 📂 Structure
devops-incident-response/
├── kubernetes/
│   ├── alert-rules.yaml              # Alert detection rules
│   └── alertmanager-config.yaml      # Alert routing config
├── scripts/
│   └── remediation-scripts.sh        # Auto-remediation scripts
├── monitoring/
│   └── prometheus-values.yaml        # Prometheus config
├── docs/
│   ├── SETUP.md                      # Installation guide
│   ├── DEMO_INSTRUCTIONS.md          # How to demo
│   └── TEAM_WORKFLOW.md              # Git workflow guide
├── README.md                         # This file
└── .gitignore                        # Files to ignore 

## 🚀 How to Run
1. Start Minikube  
2. Deploy sample app  
3. Install Prometheus  
4. Configure alerts  

## 📌 Future Scope
- Email/SMS notifications  
- AI based decision engine  
- Multi cluster support  
