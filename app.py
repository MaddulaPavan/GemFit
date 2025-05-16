import streamlit as st
from PIL import Image
import io
import base64
import ollama
from fpdf import FPDF

# Page configuration
st.set_page_config(
    page_title="Physique Pro",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 16px;
        background-color: #007bff;
        color: white;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 12px 24px;
        font-size: 16px;
        color: #343a40;
        border: 1px solid #dee2e6;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e9ecef;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background-color: #007bff;
        color: white;
        border-color: #007bff;
    }
    .block-container {
        padding: 3rem 2rem;
        max-width: 1200px;
        margin: auto;
    }
    h1 {
        color: #212529;
        font-weight: 700;
    }
    h3 {
        color: #495057;
        font-weight: 600;
    }
    .stExpander {
        border: 1px solid #ced4da;
        border-radius: 8px;
        background-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div style='text-align: center; padding: 30px 0;'>
        <h1>🏋️ Physique Pro</h1>
        <p style='color: #6c757d; font-size: 18px;'>Your AI-Powered Fitness Companion</p>
    </div>
""", unsafe_allow_html=True)

# Function to convert plan to PDF
def create_pdf(plan_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_margins(20, 20, 20)
    pdf.multi_cell(0, 10, plan_text.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# Main container
with st.container():
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        st.markdown("### Start Your Journey")
        
        use_camera = st.checkbox("Take a Photo", help="Use camera to capture physique")
        camera_image = None
        if use_camera:
            camera_image = st.camera_input("Capture your physique", key="camera")
        
        uploaded_files = st.file_uploader("Upload Physique Photos", 
                                        type=['png', 'jpg', 'jpeg'], 
                                        accept_multiple_files=True,
                                        help="Upload front, side, or back photos")
        
        with st.expander("Your Details", expanded=True):
            goal = st.selectbox("Fitness Goal", ["Build Muscle", "Lose Fat", "Get Toned", "Maintain"])
            height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170)
            weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=70)
            age = st.number_input("Age", min_value=16, max_value=100, value=25)
        
        st.button("Generate Plan", type="primary", key="generate")

    with col2:
        tab1, tab2, tab3 = st.tabs(["Preview", "Diet", "Workout"])
        
        with tab1:
            st.markdown("### Photo Preview")
            if camera_image or uploaded_files:
                cols = st.columns(min(3, len(uploaded_files) + (1 if camera_image else 0)))
                if camera_image:
                    cols[0].image(Image.open(camera_image), caption="Camera Shot", use_column_width=True)
                for i, file in enumerate(uploaded_files):
                    if i < 2:
                        cols[i + (1 if camera_image else 0)].image(Image.open(file), 
                                                                  caption=f"Photo {i+1}", 
                                                                  use_column_width=True)
            else:
                st.info("Add photos to see preview here")

        with tab2:
            st.markdown("### Diet Plan")
            if 'plan' in st.session_state:
                plan = st.session_state['plan']
                try:
                    diet_section = plan.split("### Diet Plan")[1].split("###")[0] if "### Diet Plan" in plan else plan
                    st.markdown(diet_section.strip())
                except IndexError:
                    st.markdown(plan)
                    st.warning("Diet plan format might be inconsistent")
            else:
                st.info("Generate your plan to see diet recommendations")

        with tab3:
            st.markdown("### Workout Plan")
            if 'plan' in st.session_state:
                plan = st.session_state['plan']
                try:
                    workout_section = plan.split("### Workout Plan")[1].split("###")[0] if "### Workout Plan" in plan else plan
                    st.markdown(workout_section.strip())
                except IndexError:
                    st.markdown(plan)
                    st.warning("Workout plan format might be inconsistent")
            else:
                st.info("Generate your plan to see workout schedule")

# Plan generation and PDF download
if st.session_state.get('generate', False):
    if (camera_image or uploaded_files) and height and weight and age:
        with st.spinner("Crafting your personalized plan..."):
            try:
                images_data = [camera_image.getvalue()] if camera_image else []
                images_data.extend([file.getvalue() for file in uploaded_files])
                
                response = ollama.chat(
                    model='gemma3:4b',
                    messages=[{
                        'role': 'user',
                        'content': f"""Quickly analyze physique and provide in Markdown:
                        Goal: {goal}
                        Height: {height}cm
                        Weight: {weight}kg
                        Age: {age}
                        Return:
                        ### Assessment
                        [Brief physique assessment]
                        ### Diet Plan
                        [Simple daily diet plan]
                        ### Workout Plan
                        [Basic weekly workout]""",
                        'images': images_data[:2]
                    }],
                    stream=True
                )
                full_response = ""
                for chunk in response:
                    full_response += chunk['message']['content']
                st.session_state['plan'] = full_response
                
                # Generate PDF and offer download
                pdf_bytes = create_pdf(full_response)
                st.download_button(
                    label="Download Plan as PDF",
                    data=pdf_bytes,
                    file_name="Physique_Pro_Plan.pdf",
                    mime="application/pdf",
                    key="download_pdf"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please provide all details and at least one photo!")

# Footer
st.markdown("""
    <div style='text-align: center; color: #6c757d; padding: 30px 0; font-size: 14px;'>
        Made with ❤️ by xAI | Transform Your Physique Today
    </div>
""", unsafe_allow_html=True)