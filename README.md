# Listinker API

## Prerequisites

- Python 3.12 or higher must be installed on your system.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shreyas-ITB/listiner_be.git
   cd your-repo
   ```

2. **Create a virtual environment (using Python 3.12)**
   ```bash
   python3.12 -m venv venv
   ```

3. **Activate the virtual environment**
   - On **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - On **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install the dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**

   - Rename the `.example.env` file to `.env`:
     ```bash
      mv .example.env .env
     ```
   - Open `.env` and fill in the required configuration values.

6. **Run the API**

   Navigate to the `app` directory and start the server:
   ```bash
   cd app
   python main.py
   ```

The API will start on `http://localhost:8000`
