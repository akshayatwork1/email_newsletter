import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import pandas as pd
import datetime
import os

# Customize the layout and style
st.set_page_config(page_title="Renivet Admin Panel", page_icon="📧", layout="wide")
st.markdown("""
    <style>
        body {
            background-color: #ffffff;
            font-family: 'Arial', sans-serif;
            color: #333333;
        }
        .block-container {
            padding: 2rem;
            background-color: #f9f9f9;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        h1, h2, h3 {
            color: #0073e6;
        }
    </style>
""", unsafe_allow_html=True)

# Add logo at the top of the page
st.image("R-BlackIcon.png", width=200)

# Streamlit app title
st.title("📧 Renivet Email Newsletter")

# Sidebar with options
option = st.sidebar.selectbox("Choose an Option", ["Enter Email Credentials", "View Report"])

# Email credentials input and email sending functionality
if option == "Enter Email Credentials":
    st.sidebar.header("Email Credentials")
    email = st.sidebar.text_input("Your Email")
    password = st.sidebar.text_input("Your Password", type="password")

    # Upload CSV file with recipient details
    st.header("Upload Recipient Email List")
    uploaded_file = st.file_uploader("Upload a CSV file with recipient details (columns: 'email', 'name')", type="csv")

    # Email content input
    st.header("Compose Your Email")
    subject = st.text_input("Email Subject")
    body = st.text_area("Email Body (Use placeholders like {name} to personalize)")

    # Optional attachment
    st.header("Attach a File (Optional)")
    attachment_file = st.file_uploader("Upload a file to attach", type=["pdf", "docx", "jpg", "png"])

    # Email formatting options
    st.header("Email Formatting Options")
    use_bold = st.checkbox("Bold Names")
    add_greeting = st.checkbox("Add Greeting (e.g., Dear {name})")

    # Send email button
    if st.button("Send Emails"):
        if not email or not password:
            st.error("Please enter your email and password.")
        elif uploaded_file is None:
            st.error("Please upload a CSV file with recipient details.")
        elif not subject or not body:
            st.error("Please enter both subject and body for the email.")
        else:
            try:
                # Read recipient details from CSV
                df = pd.read_csv(uploaded_file, engine='python')
                if 'email' not in df.columns or 'name' not in df.columns:
                    st.error("CSV file must contain 'email' and 'name' columns.")
                else:
                    recipient_emails = df[['email', 'name']].to_dict('records')

                    # Prepare attachment if uploaded
                    attachment_content = None
                    attachment_filename = ""
                    if attachment_file is not None:
                        attachment_content = attachment_file.read()
                        attachment_filename = attachment_file.name

                    # Set up SMTP connection for GoDaddy
                    smtp_server = "smtpout.secureserver.net"
                    smtp_port = 465  # Use port 465 for SSL/TLS

                    # Create an SMTP connection with SSL
                    server = smtplib.SMTP_SSL(smtp_server, smtp_port)

                    # Log in to the SMTP server
                    try:
                        server.login(email, password)
                    except smtplib.SMTPAuthenticationError as e:
                        st.error(f"SMTP Authentication Error: {e}")
                        st.error("Please check your email and password. If you have 2FA enabled, use an app password.")
                        server.quit()
                    else:
                        # Initialize email report
                        report_data = []
                        report_filename = 'email_report.csv'
                        if os.path.exists(report_filename):
                            report_df = pd.read_csv(report_filename)
                        else:
                            report_df = pd.DataFrame(columns=['email', 'name', 'status', 'date'])
                        
                        # Send emails
                        for recipient in recipient_emails:
                            msg = MIMEMultipart()
                            msg['From'] = email
                            msg['To'] = recipient['email']
                            msg['Subject'] = subject

                            # Customize the email body
                            personalized_body = body.replace("{name}", recipient['name'])
                            if add_greeting:
                                personalized_body = f"Dear {recipient['name']},\n\n" + personalized_body
                            if use_bold:
                                personalized_body = personalized_body.replace(recipient['name'], f"<b>{recipient['name']}</b>")

                            msg.attach(MIMEText(personalized_body, 'html'))

                            # Attach file if available
                            if attachment_content:
                                attachment = MIMEApplication(attachment_content)
                                attachment.add_header('Content-Disposition', 'attachment', filename=attachment_filename)
                                msg.attach(attachment)

                            # Send the email
                            try:
                                server.sendmail(email, recipient['email'], msg.as_string())
                                report_entry = {
                                    'email': recipient['email'],
                                    'name': recipient['name'],
                                    'status': 'Sent',
                                    'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                report_df = pd.concat([report_df, pd.DataFrame([report_entry])], ignore_index=True)
                                st.success(f"Email sent to {recipient['email']}")
                            except Exception as e:
                                report_entry = {
                                    'email': recipient['email'],
                                    'name': recipient['name'],
                                    'status': f"Failed: {e}",
                                    'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                report_df = pd.concat([report_df, pd.DataFrame([report_entry])], ignore_index=True)
                                st.error(f"Failed to send email to {recipient['email']}: {e}")

                        # Save the report
                        report_df.to_csv(report_filename, index=False)
                        st.success(f"Email report updated and saved as {report_filename}")

                        server.quit()
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Display and manage report if option is selected
elif option == "View Report":
    st.header("Email Report")
    report_filename = 'email_report.csv'
    
    # Display report if available
    if os.path.exists(report_filename):
        report_df = pd.read_csv(report_filename)
        st.dataframe(report_df)

        # Download report button
        st.download_button(
            label="Download Report",
            data=report_df.to_csv(index=False).encode('utf-8'),
            file_name='email_report.csv',
            mime='text/csv'
        )

        # Option to erase the report
        if st.button("Erase Report"):
            os.remove(report_filename)
            st.success("Report erased successfully.")
    else:
        st.info("No report available. Send some emails to generate a report.")

    # Upload new report file option
    new_report_file = st.file_uploader("Upload a new report file", type="csv")
    if new_report_file is not None:
        new_report_df = pd.read_csv(new_report_file)
        new_report_df.to_csv(report_filename, index=False)
        st.success("New report uploaded successfully.")
