import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page config
st.set_page_config(page_title="Enhanced PM Visit Analysis", layout="wide")

def calculate_weighted_scores(df, teacher_weights, student_weights):
    """Calculate weighted teacher and student scores"""
    
    def get_score(value):
        if pd.isna(value):
            return 0
        if str(value).lower() == 'yes':
            return 1
        if str(value).lower() == 'sometimes':
            return 0.5
        return 0

    # Teacher metrics with weights
    teacher_metrics = {
        'Has the teacher shared the lesson plan in advance?': teacher_weights.get('lesson_plan', 1),
        'Is the teacher moving around in the classroom?': teacher_weights.get('movement', 1),
        'Is the teacher using hands-on activities?': teacher_weights.get('hands_on', 1),
        'Is the teacher encouraging the child to answer?': teacher_weights.get('encouragement', 1)
    }
    
    # Student metrics with weights
    student_metrics = {
        'Are children asking questions?': student_weights.get('questions', 1),
        'Are children explaining their work?': student_weights.get('explanation', 1),
        'Are children involved in the activities?': student_weights.get('involvement', 1),
        'Are students helping each other to learn/do an activity?': student_weights.get('peer_help', 1)
    }
    
    try:
        # Calculate weighted scores
        teacher_scores = []
        student_scores = []
        
        for metric, weight in teacher_metrics.items():
            if metric in df.columns:
                df[f'{metric}_score'] = df[metric].apply(get_score) * weight
                teacher_scores.append(f'{metric}_score')
        
        for metric, weight in student_metrics.items():
            if metric in df.columns:
                df[f'{metric}_score'] = df[metric].apply(get_score) * weight
                student_scores.append(f'{metric}_score')
        
        if teacher_scores:
            total_teacher_weight = sum(teacher_metrics.values())
            df['teacher_score'] = (df[teacher_scores].sum(axis=1) / total_teacher_weight) * 100
            
        if student_scores:
            total_student_weight = sum(student_metrics.values())
            df['student_score'] = (df[student_scores].sum(axis=1) / total_student_weight) * 100
            
        # Calculate overall performance score
        if 'teacher_score' in df.columns and 'student_score' in df.columns:
            df['overall_score'] = (df['teacher_score'] + df['student_score']) / 2
            
    except Exception as e:
        st.error(f"Error calculating scores: {str(e)}")
        
    return df

def analyze_performance(df):
    """Analyze school performance and return insights"""
    school_metrics = df.groupby('School Name').agg({
        'teacher_score': 'mean',
        'student_score': 'mean',
        'overall_score': 'mean',
        'School Name': 'count'
    }).rename(columns={'School Name': 'visit_count'})
    
    # Calculate performance quartiles
    school_metrics['performance_quartile'] = pd.qcut(school_metrics['overall_score'], 
                                                   q=4, 
                                                   labels=['Bottom 25%', 'Lower Middle', 'Upper Middle', 'Top 25%'])
    
    return school_metrics

def main():
    st.title("Enhanced Program Manager Visit Analysis Dashboard")
    
    # Sidebar for weights and filters
    st.sidebar.header("Configuration")
    
    # Teacher weights
    st.sidebar.subheader("Teacher Observation Weights")
    teacher_weights = {
        'lesson_plan': st.sidebar.slider("Lesson Plan Sharing", 0.0, 2.0, 1.0, 0.1),
        'movement': st.sidebar.slider("Classroom Movement", 0.0, 2.0, 1.0, 0.1),
        'hands_on': st.sidebar.slider("Hands-on Activities", 0.0, 2.0, 1.0, 0.1),
        'encouragement': st.sidebar.slider("Student Encouragement", 0.0, 2.0, 1.0, 0.1)
    }
    
    # Student weights
    st.sidebar.subheader("Student Observation Weights")
    student_weights = {
        'questions': st.sidebar.slider("Asking Questions", 0.0, 2.0, 1.0, 0.1),
        'explanation': st.sidebar.slider("Explaining Work", 0.0, 2.0, 1.0, 0.1),
        'involvement': st.sidebar.slider("Activity Involvement", 0.0, 2.0, 1.0, 0.1),
        'peer_help': st.sidebar.slider("Peer Learning", 0.0, 2.0, 1.0, 0.1)
    }
    
    # File uploader
    uploaded_file = st.file_uploader("Upload PM Visit Data (Excel file)", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            # Read data
            df = pd.read_excel(uploaded_file)
            
            # Display raw data option
            if st.checkbox("Show raw data"):
                st.write("Raw Data:")
                st.write(df)
                st.write("Available columns:", df.columns.tolist())
            
            # Calculate weighted scores
            df = calculate_weighted_scores(df, teacher_weights, student_weights)
            
            # Check required columns
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
            
            # Overall metrics
            st.header("Summary Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Visits", len(filtered_df))
            with col2:
                st.metric("Unique Schools", len(filtered_df['School Name'].unique()))
            with col3:
                st.metric("Average Teacher Score", f"{filtered_df['teacher_score'].mean():.1f}%")
            with col4:
                st.metric("Average Student Score", f"{filtered_df['student_score'].mean():.1f}%")
            
            # Create tabs
            tab1, tab2, tab3, tab4 = st.tabs(["PM Visit Analysis", "Performance Overview", "School Rankings", "School Details"])
            
            with tab1:
                st.subheader("Program Manager Visit Analysis")
                
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
                
                # PM Performance Comparison
                if 'teacher_score' in filtered_df.columns:
                    pm_performance = filtered_df.groupby('Your Name').agg({
                        'teacher_score': 'mean',
                        'student_score': 'mean',
                        'overall_score': 'mean'
                    }).round(2)
                    
                    st.subheader("PM Performance Metrics")
                    st.dataframe(pm_performance)
            
            with tab2:
                st.subheader("Performance Overview")
                
                # Performance distribution
                fig_dist = px.histogram(
                    filtered_df,
                    x='overall_score',
                    nbins=20,
                    title='Distribution of School Performance Scores'
                )
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # Performance metrics by school
                performance_metrics = analyze_performance(filtered_df)
                
                # Top performing schools
                st.subheader("Top 5 Performing Schools")
                top_schools = performance_metrics.nlargest(5, 'overall_score')
                st.dataframe(top_schools.round(2))
                
                # Low performing schools
                st.subheader("Bottom 5 Performing Schools")
                bottom_schools = performance_metrics.nsmallest(5, 'overall_score')
                st.dataframe(bottom_schools.round(2))
            
            with tab3:
                st.subheader("School Rankings")
                
                # Performance quartile analysis
                quartile_counts = performance_metrics['performance_quartile'].value_counts()
                fig_quartiles = px.pie(
                    values=quartile_counts.values,
                    names=quartile_counts.index,
                    title='School Performance Distribution by Quartile'
                )
                st.plotly_chart(fig_quartiles, use_container_width=True)
                
                # Complete rankings
                st.subheader("Complete School Rankings")
                rankings = performance_metrics.sort_values('overall_score', ascending=False)
                st.dataframe(rankings.round(2))
            
            with tab4:
                st.subheader("School Details")
                
                # School selector
                selected_school = st.selectbox(
                    "Select a school for detailed analysis",
                    options=sorted(filtered_df['School Name'].unique())
                )
                
                school_data = filtered_df[filtered_df['School Name'] == selected_school]
                
                # School metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Teacher Score", f"{school_data['teacher_score'].mean():.1f}%")
                with col2:
                    st.metric("Student Score", f"{school_data['student_score'].mean():.1f}%")
                with col3:
                    st.metric("Overall Score", f"{school_data['overall_score'].mean():.1f}%")
                
                # Visit Timeline
                if 'Date of Visit ' in school_data.columns:
                    st.subheader("Visit Timeline")
                    timeline_data = school_data[['Date of Visit ', 'Your Name', 'teacher_score', 'student_score', 'overall_score']].sort_values('Date of Visit ')
                    st.dataframe(timeline_data.round(2))
                    
                    # Score trends over time
                    st.subheader("Score Trends Over Time")
                    school_data['Date of Visit '] = pd.to_datetime(school_data['Date of Visit '])
                    fig_trends = px.line(
                        school_data.sort_values('Date of Visit '),
                        x='Date of Visit ',
                        y=['teacher_score', 'student_score', 'overall_score'],
                        title='Score Trends Over Time'
                    )
                    st.plotly_chart(fig_trends, use_container_width=True)

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.write("Please check the format of your Excel file and try again.")

if __name__ == "__main__":
    main()
