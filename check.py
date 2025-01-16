import os
import requests
from bs4 import BeautifulSoup

# Read sensitive data from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        print("Message sent successfully!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

def get_visa_data():
    url = 'https://appointment.mfa.gr/inner.php/en/reservations/aero/calendar'
    
    # Define the POST request payload
    payload = {
        'bid': '65'  # Example value for 'bid'
    }  

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Origin': 'https://appointment.mfa.gr',
        'Referer': 'https://appointment.mfa.gr/inner.php/en/reservations/aero/calendar',
    }

    try:
        # Perform the POST request
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Return the HTML content of the response
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None

def check_availability(html):
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Find all days
    days = soup.find_all('td', class_='aero_bcal_tdopen')
    available_days = {}
    unavailable_days = []

    for day in days:
        # Extract the day number
        day_link = day.find('a', class_='aero_bcal_day_nonumber')
        if day_link:
            day_number = day_link.text.strip()
        else:
            continue

        # Extract the schedule data
        schedule = day.get('data-schedule', '')
        slots = schedule.split('@')

        # Check each slot for availability
        available_slots = 0
        for slot in slots:
            if slot.strip():
                time, *availability = slot.split(';')
                # Count slots with more than 0 availability
                if len(availability) > 0 and availability[-1] != '0':
                    available_slots += 1
        
        if available_slots > 0:
            available_days[day_number] = available_slots
        else:
            unavailable_days.append(day_number)

    # Return the summary of available and unavailable days
    return available_days, unavailable_days

# Example usage
if __name__ == "__main__":
    # Fetch HTML content using POST request
    html_content = get_visa_data()

    if html_content:
        # Check for availability
        available_days, unavailable_days = check_availability(html_content)

        # Build the message
        if available_days:
            days_list = "\n".join([f"Day {day}: {slots} slots available" for day, slots in available_days.items()])
            available_message = f"✅ Visa appointments available on the following days:\n{days_list}"
        else:
            available_message = "❌ No visa appointments available."

        if unavailable_days:
            unavailable_list = ", ".join(unavailable_days)
            unavailable_message = f"❌ The following days have no availability:\n{unavailable_list}"
        else:
            unavailable_message = "All days are currently available."

        # Combine messages
        final_message = f"{available_message}\n\n{unavailable_message}"

        # Send the message via Telegram
        print(final_message)
        send_telegram_message(final_message)