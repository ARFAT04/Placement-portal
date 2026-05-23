Placement Portal System

A role-based web application built using Flask that streamlines the campus placement process for students, companies, and administrators. The system allows companies to post placement drives, students to apply for opportunities, and admins to manage company approvals through a centralized dashboard.

Live Demo

🌐 Live Website:
Placement Portal Live Demo

GitHub Repository

💻 Source Code:
Placement Portal GitHub Repository

Features
Student Module
Student registration and login
View available placement drives
Apply to placement opportunities
Track applied drives
Company Module
Company registration and authentication
Company approval system managed by admin
Create and manage placement drives
View student applicants
Admin Module
Secure admin login
Approve or reject company registrations
Manage placement activities
Tech Stack
Backend: Flask (Python)
Frontend: HTML, CSS, Bootstrap
Database: SQLite
Templating Engine: Jinja2
Deployment: Render
Version Control: Git & GitHub
Project Structure
Placement-portal/
│
├── templates/
├── static/
├── app.py
├── requirements.txt
├── Procfile
└── README.md
Installation & Setup
Clone the Repository
git clone https://github.com/ARFAT04/Placement-portal.git
cd Placement-portal
Install Dependencies
pip install -r requirements.txt
Run the Application
python app.py

Open your browser and visit:

http://127.0.0.1:5000/
Admin Credentials
Email: admin@gmail.com
Password: admin123
Current Features Implemented
Role-based authentication system
Student and company registration
Company approval workflow
Placement drive creation
Student applications management
Responsive frontend using Bootstrap
Live cloud deployment using Render
Upcoming Improvements
Resume upload functionality
Better dashboard UI/UX
Search and filter system
Password encryption and validation
PostgreSQL integration
Email notifications
Improved database structure
Deployment optimization
AI-based placement recommendations (future enhancement)
Deployment

The project is deployed on Render using Gunicorn for production hosting.

Author

Arfat Ansari

B.Tech CSE Student
Interested in Web Development, AI/ML, and Backend Engineering
License

This project is developed for educational and portfolio purposes.