import os
from io import BytesIO

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="HealthAI", page_icon="X-ray", layout="centered")
st.title("HealthAI")
st.caption("Local chest X-ray analysis with PostgreSQL study history")

if "selected_study_id" not in st.session_state:
    st.session_state.selected_study_id = None

tab_analyze, tab_recent = st.tabs(["Analyze X-Ray", "Recent Studies"])

with tab_analyze:
    st.header("Analyze X-Ray")
    patient_name = st.text_input("Patient Name")
    uploaded_file = st.file_uploader(
        "Chest X-ray",
        type=["jpg", "jpeg", "png"],
        key="analysis_upload",
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded X-ray", use_container_width=True)

    if st.button("Analyze X-Ray", type="primary"):
        if not patient_name.strip():
            st.warning("Enter a patient name before analyzing the X-ray.")
        elif uploaded_file is None:
            st.warning("Choose a JPG, JPEG, or PNG X-ray first.")
        else:
            with st.spinner("Saving study and running model..."):
                try:
                    response = requests.post(
                        f"{API_URL}/studies/analyze",
                        data={"patient_name": patient_name.strip()},
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=300,
                    )
                    if response.status_code != 200:
                        detail = response.json().get("detail", response.text)
                        st.error(f"Analysis failed: {detail}")
                    else:
                        result = response.json()
                        st.session_state.selected_study_id = result["study_id"]
                        st.subheader("Prediction Results")
                        st.write(f"**Study ID:** {result['study_id']}")
                        st.write(f"**Status:** {result['status']}")
                        st.write(f"**Top Predicted Finding:** {result['predicted_condition']}")
                        st.metric("Confidence", f"{float(result['confidence']):.0%}")
                        prediction_rows = [
                            {
                                "Disease": label,
                                "Probability": f"{float(probability):.2%}",
                            }
                            for label, probability in sorted(
                                result.get("prediction_results", {}).items(),
                                key=lambda item: item[1],
                                reverse=True,
                            )
                        ]
                        st.table(prediction_rows)
                except requests.RequestException as error:
                    st.error(f"Could not connect to the backend: {error}")

with tab_recent:
    st.header("Recent Studies")
    try:
        response = requests.get(
            f"{API_URL}/studies/recent",
            params={"limit": 10},
            timeout=30,
        )
        if response.status_code != 200:
            st.error("Could not load recent studies.")
        else:
            studies = response.json()
            if not studies:
                st.info("No studies have been saved yet.")
            else:
                rows = [
                    {
                        "Study ID": study["study_id"],
                        "Patient Name": study["patient_name"] or "-",
                        "Image Name": study["image_name"],
                        "Status": study["status"],
                        "Top Predicted Finding": study["predicted_condition"] or "-",
                        "Confidence": (
                            f"{float(study['confidence']):.2%}"
                            if study["confidence"] is not None
                            else "-"
                        ),
                        "Created At": study["created_at"],
                    }
                    for study in studies
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
                study_options = {
                    f"{study['patient_name'] or '-'} - Study #{study['study_id']} - "
                    f"{study['predicted_condition'] or 'Pending'}": study["study_id"]
                    for study in studies
                }
                selected_label = st.selectbox("Select Study", list(study_options))
                if st.button("View Study Details"):
                    st.session_state.selected_study_id = study_options[selected_label]
                selected_study_id = st.session_state.selected_study_id
                try:
                    detail_response = requests.get(
                        f"{API_URL}/studies/{selected_study_id}",
                        timeout=30,
                    )
                    if detail_response.status_code != 200:
                        st.error("The selected study could not be found.")
                    else:
                        study = detail_response.json()
                        st.divider()
                        st.header("Study Details")
                        st.subheader("Study Information")
                        st.write(f"**Patient Name:** {study['patient_name'] or '-'}")
                        st.write(f"**Study ID:** {study['study_id']}")
                        st.write(f"**Date/Time:** {study['created_at']}")
                        st.write(f"**Status:** {study['status']}")
                        st.write(f"**Original Image Name:** {study['image_name']}")

                        image_response = requests.get(
                            f"{API_URL}/studies/{selected_study_id}/image",
                            timeout=30,
                        )
                        if image_response.status_code == 200:
                            st.subheader("Original X-Ray")
                            st.image(
                                Image.open(BytesIO(image_response.content)),
                                caption=study["image_name"],
                                use_container_width=True,
                            )

                        st.subheader("Prediction Summary")
                        st.write(
                            f"**Top Predicted Finding:** "
                            f"{study['predicted_condition'] or '-'}"
                        )
                        if study["confidence"] is not None:
                            st.metric("Confidence", f"{float(study['confidence']):.0%}")

                        st.subheader("All Five Prediction Results")
                        prediction_rows = [
                            {
                                "Disease": label,
                                "Probability": f"{float(probability):.2%}",
                            }
                            for label, probability in sorted(
                                study.get("prediction_results", {}).items(),
                                key=lambda item: item[1],
                                reverse=True,
                            )
                        ]
                        st.table(prediction_rows)
                except requests.RequestException as error:
                    st.error(f"Could not load study details: {error}")
    except requests.RequestException:
        st.info("Start the FastAPI backend to load recent studies.")
