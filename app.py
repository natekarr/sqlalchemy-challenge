# Import the dependencies.
from matplotlib import style
from matplotlib.dates import AutoDateLocator, AutoDateFormatter
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################


engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the existing database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to the "Measurement" and "Station" tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session
session = Session(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Precipitation data for the last 12 months<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Temperature observations for the most active station in the last 12 months<br/>"
        f"/api/v1.0/&lt;start&gt; - Min, Max, and Avg temperature for all dates greater than or equal to the start date<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Min, Max, and Avg temperature for dates between the start and end date (inclusive)<br/>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    # Calculate the date one year from the last date in the data set
    most_recent_date_str = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = datetime.strptime(most_recent_date_str, '%Y-%m-%d')
    one_year_ago = most_recent_date - timedelta(days=365)

    # Query the precipitation data for the last 12 months
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).\
        order_by(Measurement.date).all()

    # Convert the query results to a dictionary with date as the key and prcp as the value
    precipitation_data = {date: prcp for date, prcp in results}
    session.close()

    return jsonify(precipitation_data)

# Stations route
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    # Query all stations
    results = session.query(Station.station).all()

    # Convert the query results to a list
    stations_list = list(np.ravel(results))

    session.close()

    return jsonify(stations_list)

# Temperature observations route
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    # Find the most active station and its row count from the previous query
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()

    most_active_station = active_stations[0][0]  # Get the station ID of the most active station

    # Calculate the date one year from the last date in the data set
    most_recent_date_str = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = datetime.strptime(most_recent_date_str, '%Y-%m-%d')
    one_year_ago_date = most_recent_date - timedelta(days=365)

    # Query the temperature observations for the most active station in the last 12 months
    results = session.query(Measurement.tobs).\
        filter(Measurement.station == most_active_station).\
        filter(Measurement.date >= one_year_ago_date).\
        order_by(Measurement.date).all()

    # Convert the query results to a list
    tobs_list = list(np.ravel(results))

    session.close()

    return jsonify(tobs_list)

# Temperature statistics route
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temp_stats(start, end=None):
    session = Session(engine)
    # Define the start and end dates as datetime objects
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d') if end else None

    # Query the temperature observations for the specified date range
    if end_date:
        results = session.query(Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).\
            filter(Measurement.date <= end_date).\
            group_by(Measurement.date).all()
    else:
        results = session.query(Measurement.date, func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start_date).\
            group_by(Measurement.date).all()

    # Convert the query results to a list of dictionaries
    temp_stats_list = []
    for date, min_temp, avg_temp, max_temp in results:
        temp_stats_list.append({
            "Date": date,
            "Min Temperature": min_temp,
            "Average Temperature": avg_temp,
            "Max Temperature": max_temp
        })

    session.close()

    return jsonify(temp_stats_list)

if __name__ == "__main__":
    app.run(debug=True)