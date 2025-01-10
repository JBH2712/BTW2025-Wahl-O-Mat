import streamlit as st
import os
import time
import openai

# Import the predefined function
def get_assistant_response(assistant_id, message_content):
    print(f"Assistant ID: {assistant_id}")
    print(f"Message Content: {message_content}")

    if "openai_api_key" not in st.session_state or not st.session_state["openai_api_key"]:
        st.error("Bitte geben Sie Ihren OpenAI API-Schlüssel ein.")
        return ""

    openai_api_key = st.session_state["openai_api_key"]
    print(f"API Key Loaded: {bool(openai_api_key)}")

    os.environ["OPENAI_API_KEY"] = openai_api_key
    openai.api_key = openai_api_key

    # Create a new thread
    thread = openai.beta.threads.create()

    # Add a user message to the thread
    openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_content
    )

    # Create a run for the assistant
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    # Wait for the run to complete
    while run.status in ["queued", "in_progress"]:
        time.sleep(0.5)
        run = openai.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Retrieve messages from the thread
    messages = openai.beta.threads.messages.list(thread_id=thread.id)
    assistant_response = messages.data[0].content[0].text.value

    return assistant_response

# Streamlit app
st.title("Wahl-O-Mat Agent")

# API Key input
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = ""

if not st.session_state["openai_api_key"]:
    with st.sidebar:
        st.session_state["openai_api_key"] = st.text_input(
            "OpenAI API-Schlüssel eingeben:",
            type="password",
            placeholder="API-Schlüssel hier eingeben"
        )
        if st.session_state["openai_api_key"]:
            st.success("API-Schlüssel gespeichert!")

# Initialize session state for messages
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "welcome_message_shown" not in st.session_state:
    st.session_state["welcome_message_shown"] = False
if "analysis_output" not in st.session_state:
    st.session_state["analysis_output"] = None
if "party_comparison_output" not in st.session_state:
    st.session_state["party_comparison_output"] = None
if "full_chat_history" not in st.session_state:
    st.session_state["full_chat_history"] = ""
if "selected_party" not in st.session_state:
    st.session_state["selected_party"] = "CDU/CSU"

# Define Assistant IDs
MAIN_ASSISTANT_ID = "asst_xnXPdkToqybNQpN2JqEeHvoq"
ANALYSIS_ASSISTANT_ID = "asst_diIqcxsbblceAkCif2G5JoZW"
PARTY_COMPARISON_ASSISTANT_ID = "asst_h8pbx53cTHgsaxZG5TiSUQ7F"

# Display dropdown and buttons for analysis and comparison after the first message
if st.session_state["messages"]:
    st.subheader("Vergleich mit ausgewählter Partei")
    st.session_state["selected_party"] = st.selectbox(
        "Wählen Sie eine Partei aus:",
        ["CDU/CSU", "AFD", "SPD", "Die Grünen", "FDP", "Die Linken", "BSW"],
        index=["CDU/CSU", "AFD", "SPD", "Die Grünen", "FDP", "Die Linken", "BSW"].index(st.session_state["selected_party"])
    )

    # Button for analysis
    if st.button("Einordnung zu Wahlparteiprogrammen"):
        try:
            # Get the analysis assistant's response using the full chat history
            analysis_reply = get_assistant_response(ANALYSIS_ASSISTANT_ID, st.session_state["full_chat_history"])

            # Store the analysis output
            st.session_state["analysis_output"] = analysis_reply

        except Exception as e:
            st.error(f"Error during analysis: {e}")

    # Button to compare with selected party
    if st.button("Vergleiche mit ausgewählter Partei"):
        try:
            comparison_message = (
                f"Das ist die Position:\n{st.session_state['full_chat_history']}\n"
                f"Bitte ordnen Sie diese Position ein und vergleichen Sie diese Position mit dem Wahlprogramm von {st.session_state['selected_party']}.")
            party_comparison_reply = get_assistant_response(PARTY_COMPARISON_ASSISTANT_ID, comparison_message)
            st.session_state["party_comparison_output"] = party_comparison_reply
        except Exception as e:
            st.error(f"Error during party comparison: {e}")

# Display analysis output if available
if st.session_state["analysis_output"]:
    st.subheader("Analysis Output")
    st.markdown(st.session_state["analysis_output"])

# Display party comparison output if available
if st.session_state["party_comparison_output"]:
    st.subheader("Party Comparison Output")
    st.markdown(st.session_state["party_comparison_output"])

# Input for user message
st.subheader("Ihre Nachricht:")
if not st.session_state["messages"]:
    st.write("""
    Herzlich willkommen beim Wahl-O-Mat!
    Ihre Stimme zählt! Bei der Bundestagswahl geht es um die Zukunft unseres Landes – und Ihre Meinung macht den Unterschied. Der Wahl-O-Mat hilft Ihnen dabei, Ihre Überzeugungen mit den Positionen der Parteien zu vergleichen. Einfach, interaktiv und individuell.

    Durch die Beantwortung spannender Fragen zu verschiedenen Themenbereichen erhalten Sie eine klare Orientierung. Entdecken Sie, welche Parteien Ihre Ansichten teilen und treffen Sie eine informierte Wahlentscheidung.

    Lassen Sie uns gemeinsam starten: Welche Themen sind Ihnen besonders wichtig?
    """)
elif st.session_state["messages"]:
    st.write("""
    Haben Sie Lust, ein neues Thema zu besprechen? Kein Problem – schlagen Sie einfach ein neues Thema vor oder lassen Sie sich inspirieren!
    """)

user_message = st.text_area(
    "Schreiben Sie Ihre Nachricht hier ...",
    height=200,
    max_chars=None,
    placeholder="Nachricht eingeben ..."
)

# Button to send the message
if st.button("Send") and user_message:
    try:
        # Add the user message to the session state
        st.session_state["messages"].append({"role": "user", "content": user_message})

        # Get the assistant's response
        assistant_reply = get_assistant_response(MAIN_ASSISTANT_ID, user_message)

        # Add the assistant reply to the session state
        st.session_state["messages"].append({"role": "assistant", "content": assistant_reply})

        # Update the full chat history
        st.session_state["full_chat_history"] += f"User: {user_message}\nAssistant: {assistant_reply}\n"

        # Mark the welcome message as shown
        st.session_state["welcome_message_shown"] = True

    except Exception as e:
        st.error(f"Error: {e}")
        st.write(e)  # Debug output for errors

# Display chat history
st.subheader("Chat Verlauf:")
if st.session_state["messages"]:
    for message in reversed(st.session_state["messages"]):
        if message["role"] == "user":
            st.markdown(f"**You:** {message['content']}")
        elif message["role"] == "assistant":
            st.markdown(f"**Assistant:** {message['content']}")

# Clear chat button
if st.button("Chat löschen"):
    st.session_state["messages"] = []
    st.session_state["welcome_message_shown"] = False
    st.session_state["analysis_output"] = None
    st.session_state["party_comparison_output"] = None
    st.session_state["full_chat_history"] = ""
    st.success("Chat cleared!")
