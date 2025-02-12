import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(page_title="PM Visit Analysis", layout="wide")

def calculate_scores(df):
    """Calculate teacher and student scores"""
    
    def get_score(value):
        if pd.isna(value):
            return 0
        if str(value).lower() == 'yes':
            return 1
        if str(value).lower() == 'sometimes':
            return 0.5
        return 0

    # Teacher metrics
    teacher_metrics = [
        'Has the teacher shared the lesson plan in advance?',
        'Is the teacher moving around in the classroom?',
        'Is the teacher using hands-on activities?',
        'Is the teacher encouraging the child to answer?'
    ]
    
    # Student metrics
    student_metrics = [
        'Are children asking questions?',
        'Are children explaining their work?',
        'Are children involved in the activities?',
        'Are students helping each other to learn/do an activity?'
    ]
    
    # Calculate scores
    try:
        for metric in teacher_metrics:
            if metric in df.columns:
                df[f'{metric}_score'] = df[metric].apply(get_score)
        
        for metric in student_metrics:
            if metric in df.columns:
                df[f'{metric}_score'] = df[metric].apply(get_score)
        
        teacher_score_cols = [f'{metric}_score' for metric in teacher_metrics if f'{metric}_score' in df.columns]
        student_score_cols = [f'{metric}_score' for metric in student_metrics if f'{metric}_score' in df.columns]
        
        if teacher_score_cols:
            df['teacher_score'] = df[teacher_score_cols].mean(axis=1) * 100
        if student_score_cols:
            df['student_score'] = df[student_score_cols].mean(axis=1) * 100
    except Exception as e:
        st.error(f"Error calculating scores: {str(e)}")
        st.write("Available columns:", df.columns.tolist())
    
    return df

def main():
    st.title("Program Manager Visit Analysis Dashboard")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload PM Visit Data (Excel file)", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            # Read data
            df = pd.read_excel(uploaded_file)
            
            # Display raw data and columns
            if st.checkbox("Show raw data"):
                st.write("Raw Data:")
                st.write(df)
                st.write("Available columns:", df.columns.tolist())
            
            df = calculate_scores(df)
            
            # Check if required columns exist
            required_cols = ['Your Name', 'School Name']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
                st.stop()
            
            # Sidebar filters
            st.sidebar.header("Filters")
            selected_pm = st.sidebar.multiselect(
                "Select Program Managers",
                options=sorted(df['Your Name'].unique()),
                default=sorted(df['Your Name'].unique())
            )
            
            selected_schools = st.sidebar.multiselect(
                "Select Schools",
                options=sorted(df['School Name'].unique()),
                default=sorted(df['School Name'].unique())
            )
            
            # Filter data
            filtered_df = df[
                (df['Your Name'].isin(selected_pm)) &
                (df['School Name'].isin(selected_schools))
            ]
            
            # Create metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Visits", len(filtered_df))
            with col2:
                st.metric("Unique Schools", len(filtered_df['School Name'].unique()))
            
            if 'teacher_score' in filtered_df.columns:
                col3, col4 = st.columns(2)
                with col3:
                    st.metric("Average Teacher Score", f"{filtered_df['teacher_score'].mean():.1f}%")
                with col4:
                    st.metric("Average Student Score", f"{filtered_df['student_score'].mean():.1f}%")
            
            # Create tabs
            tab1, tab2 = st.tabs(["Visit Analysis", "School Details"])
            
            with tab1:
                st.subheader("Visit Analysis")
                
                # Visits by PM
                visits_by_pm = pd.DataFrame(filtered_df['Your Name'].value_counts()).reset_index()
                visits_by_pm.columns = ['Program Manager', 'Visits']
                
                fig_visits = px.bar(
                    visits_by_pm,
                    x='Program Manager',
                    y='Visits',
                    title='Number of Visits by Program Manager'
                )
                st.plotly_chart(fig_visits, use_container_width=True)
                
                # Visits by School
                visits_by_school = pd.DataFrame(filtered_df['School Name'].value_counts()).reset_index()
                visits_by_school.columns = ['School', 'Visits']
                
                fig_schools = px.bar(
                    visits_by_school,
                    x='School',
                    y='Visits',
                    title='Number of Visits by School'
                )
                fig_schools.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_schools, use_container_width=True)
            
            with tab2:
                st.subheader("School Details")
                selected_school = st.selectbox(
                    "Select a school to view details",
                    options=sorted(filtered_df['School Name'].unique())
                )
                
                school_data = filtered_df[filtered_df['School Name'] == selected_school]
                st.write(f"Number of visits: {len(school_data)}")
                
                if 'teacher_score' in school_data.columns:
                    st.write(f"Average teacher score: {school_data['teacher_score'].mean():.1f}%")
                if 'student_score' in school_data.columns:
                    st.write(f"Average student score: {school_data['student_score'].mean():.1f}%")
                
                # Show school visits timeline
                if 'Date of Visit ' in school_data.columns:
                    st.subheader("Visit Timeline")
                    timeline_data = school_data[['Date of Visit ', 'Your Name']].sort_values('Date of Visit ')
                    st.table(timeline_data)

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Please check the format of your Excel file and try again.")

if __name__ == "__main__":
    main()
