
import streamlit as st
import joblib
import pandas as pd
import plotly.express as px

# ---------------- Page Configuration ----------------
st.set_page_config(
    page_title="California Housing Price Prediction",
    page_icon="🏠",
    layout="wide"
)
# Load trained model
model = joblib.load("model.pkl")
# Load dataset
df = pd.read_csv("data/california_housing.csv")

# ---------------- Sidebar ----------------
st.sidebar.title("📌 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Home",
        "🔮 Prediction",
        "📊 Exploratory Data Analysis",
        "🌲 Feature Importance",
        "📈 Model Performance"
    ]
)

# ---------------- Home ----------------
if page == "🏠 Home":

    st.title("🏠 California Housing Price Prediction Dashboard")

    st.markdown("""
    ## Welcome!

    This dashboard was developed for the **Week 1 Statistics and Regression Assignment**.

    ### Dataset
    - California Housing Dataset
    - 20,640 observations
    - 8 input features
    - Target: Median House Value

    ### Models Implemented
    - Simple Linear Regression
    - Multiple Linear Regression
    - Random Forest Regression

    ### Tools Used
    - Python
    - Streamlit
    - Plotly
    - Scikit-Learn
    - Pandas
    - Matplotlib
    """)

    st.info("Use the navigation menu on the left to explore the dashboard.")

# ---------------- Prediction ----------------

elif page == "🔮 Prediction":

    st.title("🔮 House Price Prediction")

    st.write("Enter the property details below.")

    col1, col2 = st.columns(2)

    with col1:
        medinc = st.number_input(
            "Median Income",
            min_value=0.0,
            value=4.0,
            step=0.1
        )

        houseage = st.number_input(
            "House Age",
            min_value=1,
            value=25
        )

        averooms = st.number_input(
            "Average Rooms",
            min_value=1.0,
            value=5.5,
            step=0.1
        )

    with col2:
        latitude = st.number_input(
            "Latitude",
            value=34.0,
            step=0.1
        )

        longitude = st.number_input(
            "Longitude",
            value=-118.0,
            step=0.1
        )

    if st.button("Predict House Price"):

        input_data = pd.DataFrame({
            "MedInc": [medinc],
            "HouseAge": [houseage],
            "AveRooms": [averooms],
            "Latitude": [latitude],
            "Longitude": [longitude]
        })

        prediction = model.predict(input_data)[0]

        st.success(f"Predicted Median House Value: ${prediction * 100000:,.0f}")

# ---------------- EDA ----------------

elif page == "📊 Exploratory Data Analysis":

    st.title("📊 Exploratory Data Analysis")

    chart = st.selectbox(
        "Choose a visualization",
        [
            "House Price Distribution",
            "Median Income vs House Price",
            "Correlation Heatmap"
        ]
    )

    if chart == "House Price Distribution":

        fig = px.histogram(
            df,
            x="MedHouseVal",
            nbins=40,
            title="Distribution of Median House Value"
        )

        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Median Income vs House Price":

        fig = px.scatter(
            df.sample(2000, random_state=33),
            x="MedInc",
            y="MedHouseVal",
            title="Median Income vs House Value",
            trendline="ols"
        )

        st.plotly_chart(fig, use_container_width=True)

    elif chart == "Correlation Heatmap":

        corr = df.corr(numeric_only=True)

        fig = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale="RdBu_r",
            title="Correlation Heatmap"
        )

        st.plotly_chart(fig, use_container_width=True)

# ---------------- Feature Importance ----------------
elif page == "🌲 Feature Importance":

    st.title("🌲 Feature Importance")

    importance = pd.read_csv("feature_importance.csv")

    fig = px.bar(
        importance,
        x="Importance",
        y="Feature",
        orientation="h",
        title="Random Forest Feature Importance"
    )

    st.plotly_chart(fig, use_container_width=True)
# ---------------- Model Performance ----------------
elif page == "📈 Model Performance":

    st.title("📈 Model Performance")

    results = pd.read_csv("model_comparison.csv")

    st.dataframe(results, use_container_width=True)

    fig = px.bar(
        results,
        x="Model",
        y="R² Score",
        title="Model Performance (R² Score)"
    )

    st.plotly_chart(fig, use_container_width=True)