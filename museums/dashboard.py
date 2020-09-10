import lxml.html as lh
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression
from wikipedia import wikipedia


def get_museum_wikipedia_table():
    page = wikipedia.page("List_of_most_visited_museums")
    page_html = page.html()

    table = lh.fromstring(page_html)
    df = pd.read_html(page_html)[0]

    countries = table.xpath("//tr/td/span[@class='flagicon']/a/@title")

    assert len(countries) == len(df)

    df["Country"] = countries
    df.rename(columns={"Country flag, city": "City"}, inplace=True)
    return df


def get_cities_table():
    cities_df = pd.read_html("https://worldpopulationreview.com/world-cities")[0]
    cities_df.rename(columns={"Name": "City"}, inplace=True)

    CITIES_TO_RENAME = [
        ["Taibei", "Taipei"],
        ["Washington", "Washington, D.C."],
        ["New York", "New York City"],
        ["Rio De Janeiro", "Rio de Janeiro"],
        ["Xianyang Shaanxi", "Xi'an"],  # TODO To be verified that it is the same city.
        ["Taizhong", "Taichung"],  # TODO To be verified that it is the same city.
    ]

    COUNTRIES_TO_RENAME = [
        ["Republic Of Korea", "South Korea"],
        ["Russian Federation", "Russia"],
        ["China, Taiwan Province Of China", "Taiwan"],
    ]

    MISSING_CITIES = [
        {
            "City": "Oświęcim",
            "Country": "Poland",
            "2020 Population": 39057,
        },  # https://en.wikipedia.org/wiki/O%C5%9Bwi%C4%99cim
        {
            "City": "Vatican City",
            "Country": "Vatican City",
            "2020 Population": 618,
        },  # https://www.vaticanstate.va/it/stato-governo/note-generali/popolazione.html
    ]

    for old_name, new_name in CITIES_TO_RENAME:
        cities_df.loc[cities_df.City == old_name, "City"] = new_name

    for old_name, new_name in COUNTRIES_TO_RENAME:
        cities_df.loc[cities_df.Country == old_name, "Country"] = new_name

    for c in MISSING_CITIES:
        cities_df = cities_df.append(c, ignore_index=True)

    # Remove Suzhou double entry, keeping the biggest
    cities_df.drop_duplicates(subset="City", keep="first", inplace=True)

    return cities_df


@st.cache  # @st.cache allows streamlit to memoize function return values and prevent reevaluating at each page change.
def load_museums_df():
    museums_df = get_museum_wikipedia_table()
    cities_df = get_cities_table()

    # Make sure all countries from museums_df are present in cities_df
    museum_df_countries = set(museums_df.Country)
    cities_df_countries = set(cities_df.Country)
    diff = museum_df_countries - cities_df_countries
    if len(diff) > 0:
        print("Missing cities info :")
        print(museums_df.query("City not in @cities_df.City"))
        print(diff)
        raise ValueError(
            "Missing city info. A country from the museum list cannot be found in the cities list.",
            diff,
        )

    # Merge museums with cities table
    result_df = pd.merge(
        museums_df,
        cities_df,
        how="left",
        left_on=["City", "Country"],
        right_on=["City", "Country"],
    )

    result_df = result_df[
        ["Name", "City", "Country", "Visitors per year", "2020 Population"]
    ].copy()
    result_df.rename(columns={"2020 Population": "Population"}, inplace=True)

    return result_df


@st.cache  # @st.cache allows streamlit to memoize function return values and prevent reevaluating at each page change.
def load_model(df):
    model = LinearRegression()
    X = df[["Population"]]
    y = df["Visitors per year"]

    model.fit(X, y)

    return model


def predict_visitors(model):
    st.write(
        "# Enter a city population\nto get an estimated number of museum annual visitors:"
    )
    city_pop = st.number_input("City pop (in M)", value=0, min_value=0, step=1)
    city_pop *= 1e6
    predicted_museum_visitors = int(model.predict([[city_pop]])[0])
    st.write("Estimated number of annual visitors:\n# ", predicted_museum_visitors)

    return city_pop, predicted_museum_visitors


def plot(df, model, x, y_hat):
    X = df["Population"].values
    x_range = np.linspace(X.min(), X.max(), 100)
    y_range = model.predict(x_range.reshape((-1, 1)))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Population"],
            y=df["Visitors per year"],
            opacity=0.65,
            mode="markers",
            text=[
                f"{name} - {city}, {country}"
                for name, city, country in zip(
                    df["Name"].values, df["City"].values, df["Country"].values
                )
            ],
        )
    )
    fig.add_trace(go.Scatter(x=x_range, y=y_range, name="Linear Regression"))
    fig.update_layout(
        annotations=[
            dict(x=x, y=y_hat, text=f"Prediction={y_hat}", arrowhead=2, ax=0, ay=-75)
        ]
    )
    st.plotly_chart(fig)


def main():
    df = load_museums_df()
    model = load_model(df)

    st.markdown("# Museums Annual Visitors Estimator\n")

    st.markdown("Museums annual visitors:")
    st.dataframe(df, width=1000)

    x, y_hat = predict_visitors(model)

    plot(df, model, x, y_hat)


if __name__ == "__main__":
    main()
