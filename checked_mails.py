import streamlit as st
import pymongo


# Database connections
client=pymongo.MongoClient("mongodb+srv://shubhamsrivastava:hzQ2IckGfmoJb4XS@emailreader.elzbauk.mongodb.net/")
# Database
db= client['EmailDatabase']
collection_clients = db["Emails"]
collection_usersdetail = db['Users']
collection_searchwords= db['Searchwords']

def main():
    
    st.subheader("Processed Mails")    
    if 'load_query' not in st.session_state:
        st.session_state['load_query'] = {}
    # Values to store query results, total number of mails and unchecked mails
    query={}
    total_mail=0
    unread_mail=0
    
    # Adding a search bar
    search_value = st.sidebar.text_input("Search:", "")
    input_search = st.sidebar.button("Search")
    if input_search:
        #query = {"$text": {"$search": search_value}}
        query = {
    "$or": [
        {"subject": {"$regex": search_value, "$options": "i"}},
        {"description": {"$regex": search_value, "$options": "i"}}
    ]
}

        st.session_state['load_query']= query
    #    search(query)
    st.sidebar.write("----------------------------------")
    

# Creating a date search
    selected_date = st.sidebar.date_input("Select a Date")
    date_search = st.sidebar.button("Date Search")
    if date_search:
        query = {"date": selected_date.strftime("%d %b %Y")}
        st.session_state['load_query']= query

    #    search(query)
    st.sidebar.write("----------------------------------")

    # Query to extract data from the "Searchwords" collection
    search_words_data = collection_searchwords.find({}, {"_id": 0, "keyword": 1})

    # Extract "keyword" values and store them in a list
    search_words_list = [item["keyword"] for item in search_words_data]
    
    # List of predefined items
    predefined_items = search_words_list
    # Add a custom item in the sidebar
    search_word = st.sidebar.text_input("You can create or remove custom search words")
    if st.sidebar.button("Create"):
        collection_searchwords.insert_one({"keyword": search_word})
        st.sidebar.write("search word created")
        st.experimental_rerun()
    if st.sidebar.button("Remove"):
        try:
            # Delete the document with the specified keyword
            collection_searchwords.delete_one({"keyword": search_word})
            st.sidebar.write("search word removed")    
        except:
            st.sidebar.write("search word doesnot exists")
        st.experimental_rerun()
        
    st.sidebar.write("----------------------------------")
    # Display predefined items in the sidebar as clickable buttons
    for item in predefined_items:
        # item_search = st.sidebar.button(item)
        if st.sidebar.button(item):
            # Create the query using $text operator
            query = {"$or": [{"subject": {"$regex": item, "$options": "i"}},
        {"description": {"$regex": item, "$options": "i"}}]}
            st.session_state['load_query']= query

    # Searching documents using query
    search_results = collection_clients.find(query).sort("date", pymongo.DESCENDING)
    count_results = collection_clients.find(query)
    # Get the number of search results
    total_mail = collection_clients.count_documents(query)
    unread_mail=0
    for docs in count_results:
            if docs.get("status")!='unchecked':  # If status is False (unread)
                unread_mail += 1
    st.write("Total Records:", total_mail)
    st.write("Processed Mails:",unread_mail)
    st.write("------------------------------------------")
    #terating over individual documents extracted through the query
    for doc in search_results:
        if doc.get("status")!='unchecked':
            st.write("Date:", doc.get("date"))
            st.write("Reciever:", doc.get("reciever"))
            st.write("Sender:", doc.get("sender"))
            st.write("Subject:", doc.get("subject"))
            st.write("Emails:", doc.get("emails"))
            st.write("Job Titles:", doc.get("designations"))
            st.write("Remarks:", doc.get('remark'))
            with st.expander(" View Details"):
                st.write("Content:", doc.get("description"))
                
                additional_info = st.text_area("Additional Information:",doc.get("info"),height=100,key=f"additional_info_{doc['_id']}")
                # option=["Unchecked", "checked"]
                
                # Checkbox to mark email as Read
                update_button_key = f"update_button_{doc['_id']}"
                #load = st.button("Update",update_button_key)
                update_button = st.button("Update", key=update_button_key)
                if update_button:
                    new_info = additional_info
                
                # Update the additional information field in the MongoDB document
                    collection_clients.update_one(
                {"_id": doc["_id"]},
                {"$set": {"info": new_info}})
                    st.success("Additional information updated successfully!")
                    st.experimental_rerun()
                
                unread_checkbox_key = f"read_checkbox_{doc['_id']}"
                un_read = st.checkbox("Mark as Unread", key=unread_checkbox_key)    

                if un_read:
                    
                    collection_clients.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "unchecked"}})
                    st.success("Status updated successfully!")
                    st.experimental_rerun()
                
                
                delete_button_key = f"delete_button_{doc['_id']}"
                delete_button = st.button("Delete", key= delete_button_key)
                if delete_button:
                    result = collection_clients.delete_one({"_id": doc["_id"]})
                    if result.deleted_count > 0:
                        st.success("Document deleted successfully.")
                    else:
                        st.error("Failed to delete document.")
                    st.experimental_rerun()

            st.write("--------------------------------------------------------------------------")
    

if __name__ == "__main__":
    main()

