# RockFlow

RockFlow is an innovative project that combines cutting-edge technology with financial advisory services to create a seamless, automated investment management platform.

## Overview

RockFlow leverages advanced algorithms and machine learning to provide personalized investment recommendations and portfolio management solutions. Our platform aims to democratize access to professional-grade financial advice while maintaining the highest standards of security and compliance.

## Features

- Automated portfolio management
- Personalized investment recommendations
- Real-time market analysis
- Secure user authentication
- Interactive dashboard interface
- Comprehensive reporting tools

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 14.x or higher
- PostgreSQL 12.x or higher

### Installation

1. Clone the repository:
```bash
git clone https://gitlab.oit.duke.edu/gh153/512_project_team6_testing.git
cd rockflow
```

2. Install dependencies:
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the development server:
```bash
# Backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

## Project Structure

```
rockflow/
├── backend/           # Django backend
├── frontend/         # React frontend
├── docs/            # Documentation
├── tests/           # Test files
└── requirements.txt  # Python dependencies
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Testing

Run the test suite:

```bash
# Backend tests
python manage.py test

# Frontend tests
cd frontend
npm test
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Team

- Team 6 - Duke University
- Course: ECE 512

## Support

For support, please open an issue in the GitLab repository or contact the development team.
# RockFlow
# RockFlow
