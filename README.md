# SAFEOPS+

*Ensuring Safety, Empowering Innovation, Securing the Future*


## Overview

SafeOps+ is an all-in-one developer toolset focused on enhancing operational safety, security, and compliance within complex system architectures. It streamlines incident management, automates vulnerability detection, and enforces security standards across repositories, configurations, and infrastructure components.

## Why SafeOps+?

This project helps developers build resilient, compliant, and secure systems with ease. The core features include:

###  Security & Compliance Checks
Validate files, repositories, and infrastructure against standards like NIST, ISO, GDPR, and HIPAA.

###  Vulnerability & Risk Assessment
Perform real-time scans of GitHub repositories and visualize risk levels.

###  CI/CD Integration
Automate security scans within GitLab CI, Jenkins, and GitHub Actions pipelines.

###  Intuitive Frontend
React-based UI with Tailwind CSS, supporting dynamic dashboards and user management.

###  Robust Backend
Flask API, cloud infrastructure, and database integrations for scalable operations.

###  Incident & Performance Monitoring
Collect web metrics and ensure high-quality user experiences.

## Built With

![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![JSON](https://img.shields.io/badge/JSON-000000?style=for-the-badge&logo=json&logoColor=white)
![npm](https://img.shields.io/badge/npm-CB3837?style=for-the-badge&logo=npm&logoColor=white)
![Autoprefixer](https://img.shields.io/badge/Autoprefixer-DD3A0A?style=for-the-badge&logo=autoprefixer&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-623CE4?style=for-the-badge&logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chart.js&logoColor=white)
## Software Architecture 
<img width="1532" height="700" alt="Image" src="https://github.com/user-attachments/assets/53d2cfab-8de4-4f09-bb09-4e7b171dcb04" />

## Table of Contents

- [Overview](#overview)
- [Software Architecture ](#software-architecture)
- [Swagger API Documentation](#swagger-api-documentation)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Video](#video)
- [Contributing](#contributing)
- [Contact](#contact)
- [License](#license)

---

##  Swagger API Documentation

The **SafeOps+ API** is fully documented with Swagger UI to make testing and understanding endpoints effortless.

**Swagger URL:**  
 [http://localhost:5000/apidocs/](http://localhost:5000/apidocs/)

This documentation provides:
- A visual overview of all available API endpoints.
- The ability to test endpoints directly from the browser.
- Automatically generated schemas and request/response models.

###  Example Screens

####  Swagger Dashboard – Overview of All Endpoints  
![Swagger Dashboard](https://github.com/user-attachments/assets/5a43c3bc-74e9-4c49-b02a-7ba9730ebf76)

####  Login Endpoint – Example Input and Parameters  
![Login Endpoint](https://github.com/user-attachments/assets/1364beae-3832-4a92-8731-2750a6dc7d25)

####  Models & Schemas – Data Structures for Each Endpoint  
![Models and Schemas](https://github.com/user-attachments/assets/69bf353c-d005-4f5f-8649-e970b10768e8)


---
## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- **Node.js** (v16.0.0 or higher)
- **Python** (v3.8 or higher)
- **Docker** (optional, for containerized deployment)
- **Git** for version control
- **npm** or **yarn** package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MonsefRH/SafeOps
   ```



2. **Environment setup in the backend**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

## Usage



## Start the full application (backend, frontend, and database) with:

1. Build the application

```bash
docker compose build
```


2. Run the application

```bash
docker compose up -d
```


 3. View logs (Postgres)

```bash
docker compose logs -f postgres
```
4. View logs (Backend)

```bash
docker compose logs -f backend
```



 **Access the application**
   - Frontend: `http://localhost:3000`
   - API: `http://localhost:5000`


 **Demo Video**  
 
https://github.com/user-attachments/assets/73c6a73c-dbdf-4698-b5f9-e1e1b639eddd


## Contributing

We welcome contributions to SafeOps+! Please follow these steps:

1. Fork the repository
2. Create a feature branch 
3. Commit your changes 
4. Push to the branch 
5. Open a Pull Request


# Contact

For any questions, feedback, or support, feel free to reach out:

## Email:
- [safeops.suupport@gmail.com](mailto:safeops.suupport@gmail.com)
- [elbadourii.youssef@gmail.com](mailto:elbadourii.youssef@gmail.com)
- [rhouddanimonsef@gmail.com](mailto:rhouddanimonsef@gmail.com)
- [tahallianas74@gmail.com](mailto:tahallianas74@gmail.com)

## LinkedIn:
- [Youssef El BADOURI](https://www.linkedin.com/in/youssef-el-badouri/)
- [Monsef RHOUDDANI](https://www.linkedin.com/in/monsef-rhouddani/)
- [Anas Tahalli](https://www.linkedin.com/in/anas-tahalli-327786226/)


## License


This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.




**SafeOps** - Ensuring Safety, Empowering Innovation, Securing the Future 
