# SAFEOPS

*Ensuring Safety, Empowering Innovation, Securing the Future*


## Overview

SafeOps is an all-in-one developer toolset focused on enhancing operational safety, security, and compliance within complex system architectures. It streamlines incident management, automates vulnerability detection, and enforces security standards across repositories, configurations, and infrastructure components.

## Why SafeOps?

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
![Markdown](https://img.shields.io/badge/Markdown-000000?style=for-the-badge&logo=markdown&logoColor=white)
![npm](https://img.shields.io/badge/npm-CB3837?style=for-the-badge&logo=npm&logoColor=white)
![Autoprefixer](https://img.shields.io/badge/Autoprefixer-DD3A0A?style=for-the-badge&logo=autoprefixer&logoColor=white)
![PostCSS](https://img.shields.io/badge/PostCSS-DD3A0A?style=for-the-badge&logo=postcss&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-623CE4?style=for-the-badge&logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chart.js&logoColor=white)

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

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

2. **Install dependencies**
   ```bash
   # Install frontend dependencies
   cd frontend

   npm install
   
   # Install Python backend dependencies
   cd backend

   pip install -r requirements.txt
   ```

3. **Environment setup**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your configuration
   nano .env
   ```

 4. **Database Setup**

 ***Step 1: Connect to PostgreSQL***
```bash
psql -U postgres
```

***Step 2: Create Database***
```sql
-- In the psql terminal
CREATE DATABASE safeops;
\q
```

***Step 4: Create the admin user***
```bash
psql -U postgres -d safeops -f tables.txt

```
***Step 3: Import Database Schema***
```bash
psql -U postgres

-- In the psql terminal

INSERT INTO users  (name, email, password, role)
VALUES (
    'Admin ',
    'admin@example.com',
    '$2b$12$YOUR_HASHED_PASSWORD', -- Replace with a bcrypt hashed password
    'admin'
);
```
---

**Note:** Replace `postgres` with your actual PostgreSQL username.

## Usage

### Development Mode

1. **Start the backend server**
   ```bash
   python app.py
   ```

2. **Start the frontend development server**
   ```bash
   npm start
   ```

3. **Access the application**
   - Frontend: `http://localhost:3000`
   - API: `http://localhost:5000`


▶️ **Demo Video**  
 
[ Cliquez ici pour voir la démonstration](https://www.dropbox.com/scl/fi/2xxd7shzfgwcnj56fc3fy/Safeops.mp4?rlkey=9j4vj7l5xl98d1rvzvbrjsxbh&st=5mom5bms&raw=1)
)

## Contributing

We welcome contributions to SafeOps! Please follow these steps:

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
