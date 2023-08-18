import streamlit as st
import datetime as dt
from dateutil import parser
import pymongo
import imaplib
import email
import re
import unchecked_mails, checked_mails



#Database connections
client=pymongo.MongoClient("mongodb+srv://shubhamsrivastava:hzQ2IckGfmoJb4XS@emailreader.elzbauk.mongodb.net/")
#client = pymongo.MongoClient(**st.secrets["mongo"])
#client=pymongo.MongoClient("mongodb+srv://st.secrets.db_username:st.secrets.db_password@emailreader.elzbauk.mongodb.net/")

#  Database
db= client['EmailDatabase']
collection_clients = db["Emails"]
collection_usersdetail = db['Users']
collection_searchwords= db['Searchwords']
#
#secrets.db_credentials.password



def get_user_credentials(emailid):
    user_data = collection_usersdetail.find_one({"emailid": emailid})
    if user_data:
        passwordid = user_data.get("password")
        imap_server_id = user_data.get("imapserver")
        return passwordid, imap_server_id
    else:
        return None, None

# Add code to display read mails
def home_page():
    st.subheader("Registered Users")
    # Query the collection and project emailid and username fields
    query = {}
    projection = {"emailid": 1, "username": 1, "_id": 0}
    results = collection_usersdetail.find(query, projection)
    # Display the results as a list
    for result in results:
        st.write(f"User: <span style='color: orange;'>{result['username']}</span>,"
                 f"<span style='margin-right: 10px;'></span>"
             f"Email ID: <span style='color: green;'>{result['emailid']}</span>", unsafe_allow_html=True)
        st.write("")


    st.sidebar.subheader("Auto-Extract Mails")
    status=""
    passwordid=""
    imap_server_id=""

    emailid = st.sidebar.text_input("Enter Email Id")
    if st.sidebar.button("Read Mails"):
        passwordid, imap_server_id = get_user_credentials(emailid)
        # Connect to inbox
        try:
                imap_server = imaplib.IMAP4_SSL(host=imap_server_id)
                imap_server.login(emailid, passwordid)
                #Default select is for inbox
                imap_server.select()
                _, message_numbers_raw = imap_server.search(None, 'ALL')
                count=0
                for message_number in message_numbers_raw[0].split():
                    count=0
                    _, msg = imap_server.fetch(message_number, '(RFC822)')

                    # Rest of your email processing code
                    message = email.message_from_bytes(msg[0][1])
                    content = "" 
                    for part in message.walk():
                        if (part.get_content_type() == "text/plain"):
                            
                            content = part.get_payload()
                    
                    
                    # Format the date to match the desired format
                    parsed_date = parser.parse(message["date"])
                    formatted_date = parsed_date.strftime("%d %b %Y")  

                    existing_document = collection_clients.find_one({
                        "sender":message["from"], "reciever":message["to"] , "date":formatted_date,
                        "subject":message["subject"], "description":content })
                    if existing_document is None:
                            # Document doesn't exist, insert data into the collection
                            # Your email,designation, remarks from content extract_job_title
                            d, e, r = extract_job_title(content)
                            designation, emails, remarks = list(set(d)),list(set(e)),list(set(r))
 
                            new_document = {"sender":message["from"], "reciever":message["to"] , "date":formatted_date ,
                            "subject":message["subject"], "description":content, "designations":designation,"emails":emails, "remark":remarks , "status":"unchecked"}
                            collection_clients.insert_one(new_document)
                            status = "Emails inserted successfully into Database" 

                    else: 
                            count+=1
                    if (count>0):
                            status= "Inbox is already updated"

        except imaplib.IMAP4.error:
                    status = "Login failed. Please enter correct credentials."

        st.sidebar.write(status)

        try:
    

                imap_server = imaplib.IMAP4_SSL(host=imap_server_id)
                imap_server.login(emailid, passwordid)
                #Default select is for inbox
                imap_server.select('[Gmail]/Spam')
                _, message_numbers_raw = imap_server.search(None, 'ALL')
                count=0
                for message_number in message_numbers_raw[0].split():
                    count=0
                    _, msg = imap_server.fetch(message_number, '(RFC822)')

                     # Rest of your email processing code
                    message = email.message_from_bytes(msg[0][1])
                    content = "" 
                    for part in message.walk():
                        if (part.get_content_type() == "text/plain"):
                            
                            content = part.get_payload()

                    # Format the date to match the desired format
                    parsed_date = parser.parse(message["date"])
                    formatted_date = parsed_date.strftime("%d %b %Y")  
                    existing_document = collection_clients.find_one({
                        "sender":message["from"], "reciever":message["to"] , "date":formatted_date,
                        "subject":message["subject"], "description":content })
                    
                    if existing_document is None:
                            # Document doesn't exist, insert data into the collection
                            # Your email,designation, remarks from content extract_job_title
                            d, e, r = extract_job_title(content)
                            designation, emails, remarks = list(set(d)),list(set(e)),list(set(r))

                            new_document = {"sender":message["from"], "reciever":message["to"] , "date":formatted_date ,
                            "subject":message["subject"], "description":content, "designations":designation,"emails":emails, "remark":remarks , "status":"unchecked"}
                            collection_clients.insert_one(new_document)
                            status = "Spam inserted successfully into Database" 

                    else: 
                            count+=1
                if (count>0):
                            status= "Spam is already updated"

        except imaplib.IMAP4.error:
                    status = "Spam could not be extracted."

        st.sidebar.write(status)


def extract_job_title(content):
    remarks=[]
    job_list=[]
    emails=[]
    # Create a Collection so that keywords can be added and removed in words_to_find
    # Query to extract data from the "Searchwords" collection
    search_words_data = collection_searchwords.find({}, {"_id": 0, "keyword": 1})

    # Extract "keyword" values and store them in a list
    search_words_list = [item["keyword"] for item in search_words_data]
    words_to_find = search_words_list
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    job_title_keywords = ["job title","job role","role","job", "position"]
    emails = re.findall(email_pattern, content)
    job_title_pattern = rf'({"|".join(job_title_keywords)})\s*(?:of|as|is)?\s*(\w+\s*\w*)'
    job_title_match = re.findall(job_title_pattern, content, flags=re.I)
    for word in words_to_find:
        if re.search(r'\b' + re.escape(word) + r'\b', content, re.IGNORECASE):
            remarks.append(word)
    for match in job_title_match:
        job_title, name = match
        job_list.append(name)
    return job_list, emails, remarks
        


def main():
    
    # Radio buttons to navigate between pages
    st.sidebar.subheader("Navigation Menu")
    navigation = st.sidebar.radio("", ("Home", "Fresh Emails", "Processed Emails"))
    st.sidebar.write("----------------------------------")
    if navigation == "Home":
        home_page()
    elif navigation == "Fresh Emails":
        unchecked_mails.main()
        #st.write("unchecked")
    elif navigation == "Processed Emails":
        checked_mails.main()
        #st.write("checked")

if __name__ == "__main__":
    main()
