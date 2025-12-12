Hospital Patient Record Management System

📋 Project Overview
A comprehensive Hospital Patient Record Management System with a modern web-based frontend and RESTful API backend. 
The system allows healthcare professionals to efficiently manage patient records, track admissions and discharges, and generate reports.

✨ Features

🏥 Patient Management

  ✅ Add new patients with complete medical records
  
  ✅ View all patients with advanced filtering
  
  ✅ Search patients by name, ID, or condition
  
  ✅ Update patient information
  
  ✅ Delete patient records
  
  ✅ Discharge patients with date tracking

📊 Dashboard & Analytics

  ✅ Real-time statistics (Admitted/Discharged/Total Patients)
  
  ✅ Weekly admission trends visualization
  
  ✅ Common conditions analysis
  
  ✅ Recent activity tracking
  
  ✅ Interactive charts and graphs

🔧 Advanced Features
  ✅ Role-based access (Admin/Doctor/Nurse)
  
  ✅ Export data to CSV/JSON formats
  
  ✅ Print patient records and reports
  
  ✅ Notification system
  
  ✅ Responsive design for all devices
  
  ✅ Database backup and restore

🏗️ System Architecture
  
  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
  │   Frontend      │    │   Backend API   │    │   MySQL         │
  │   (HTML/CSS/JS) │◄──►│   (Flask)       │◄──►│   Database      │
  └─────────────────┘    └─────────────────┘    └─────────────────┘
  
📁 Project Structure
text
hospital-system/
├── hospital_system.py           
├── requirements.txt          
├── hospital_frontend.html           
└── README.md                     

Available endpoints:
  GET  /api/health        - Health check
  
  GET  /api/dashboard     - Dashboard data
  
  GET  /api/patients      - List patients
  
  POST /api/patients      - Add patient
  
  PUT  /api/patients/:id  - Update patient
  
  DEL  /api/patients/:id  - Delete patient
