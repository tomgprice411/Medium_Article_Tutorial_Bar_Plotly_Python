import pandas as pd
import plotly.graph_objects as go
import os
from plotly.subplots import make_subplots



#######################
# Data Transformation #
#######################

##########
# Step 1 #
##########

os.chdir("/mnt/c/Users/tom_p/Spira_Analytics/Medium_Articles/Plotly_Guide_Bar_Chart")
#read data
df_raw = pd.read_csv("Pakistan Largest Ecommerce Dataset.csv")

#only include columns that we are interested in and drop NA's from those columns
df_raw = df_raw[["item_id", "status", "created_at", "price", "qty_ordered", "grand_total", "category_name_1", "discount_amount"]]
df_raw.dropna(inplace = True)

#convert date to datetime
df_raw["created_at"] = pd.to_datetime(df_raw["created_at"])

#only use completed, received or paid orders
df_raw = df_raw.loc[df_raw["status"].isin(["complete", "received", "paid"])]

#we will make the assumption that grand total should be price multiplied by quantity ordered 
#minus discount amount
df_raw["grand_total_calc"] = (df_raw["price"] * df_raw["qty_ordered"]) - df_raw["discount_amount"]
df_raw["grand_total_diff"] = df_raw["grand_total_calc"] - df_raw["grand_total"]

#some of the grand total figures look way out compared to our calculation 
#for the purpose of our visual we will go with our assumed calculation
df_raw["grand_total"] = df_raw["grand_total_calc"]
df_raw.drop(columns = ["grand_total_calc", "grand_total_diff"], inplace = True)

#filter the data so we only have the dates we are interested in
df_raw = df_raw.loc[(df_raw["created_at"].between("2017-06-01", "2017-08-28")) | (df_raw["created_at"].between("2018-06-01", "2018-08-28"))].copy()

#add in variable indicating this year and last year's data
df_raw["season_ind"] = "Last Year"
df_raw.loc[df_raw["created_at"] > "2018-01-01", "season_ind"] = "This Year"

#transform the data so we can acquire the metrics we want to illustrate
df = df_raw.groupby(["season_ind", "category_name_1"]).agg(items_ord = ("qty_ordered", "sum"),
                                                        sales = ("grand_total", "sum")).reset_index()

#transform the dataframe so that the rows shows all the metrics for each individual category
df = df.pivot(columns = "season_ind", 
        index = "category_name_1",
        values = ["items_ord", "sales"]).reset_index()

#rename the columns to remove the multi index
df.columns = ["category_name", "items_ord_ly", "items_ord_ty", "sales_ly", "sales_ty"]

#calculate the average selling price
df["avg_rsp_ly"] = df["sales_ly"] / df["items_ord_ly"]
df["avg_rsp_ty"] = df["sales_ty"] / df["items_ord_ty"]

#calculate the year on year variances
df["items_ord_variance_abs"] = df["items_ord_ty"] - df["items_ord_ly"]
df["items_ord_variance_%"] = df["items_ord_variance_abs"] / df["items_ord_ly"]

df["sales_variance_abs"] = df["sales_ty"] - df["sales_ly"]
df["sales_variance_%"] = df["sales_variance_abs"] / df["sales_ly"]

df["avg_rsp_variance_abs"] = df["avg_rsp_ty"] - df["avg_rsp_ly"]
df["avg_rsp_variance_%"] = df["avg_rsp_variance_abs"] / df["avg_rsp_ly"]

#drop \N category
df.drop(index = df.loc[df["category_name"] == r"\N"].index, inplace = True)

######################
# Data Visualisation #
######################

##########
# Step 2 #
##########


fig = go.Figure()
fig.add_trace(go.Bar(x = df["sales_variance_abs"],
                    y = df["category_name"],
                    orientation = "h")) #set orientation to horizontal because we want to flip the x and y-axis
fig.show()


##########
# Step 3 #
##########

# we want to sort the categories from highest to lowest for year on year sales variance
CATEGORY_ORDER = df.sort_values(by = "sales_variance_abs")["category_name"].tolist()

fig = go.Figure()

fig.add_trace(go.Bar(x = df["sales_variance_abs"],
                    y = df["category_name"],
                    orientation = "h",
                    ))

fig.update_layout(plot_bgcolor = "white",
                    font = dict(color = "#909497"),
                    title = dict(text = "Year on Year Sales Variance by Category for Pakistan Ecommerce Stores"),
                    xaxis = dict(title = "Sales Variance (Abs)", linecolor = "#909497", tickprefix = "&#8377;"), #tick prefix is the html code for Rupee
                    yaxis = dict(title = "Product Category", tickformat = ",", linecolor = "#909497",
                                categoryorder = "array", categoryarray = CATEGORY_ORDER)) #apply our custom category order

fig.show()


##########
# Step 4 #
##########

#transform the dataframe so that we have access to the absolute variances in sales, items ordered and avg rsp
df2 = df.melt(id_vars = ["category_name"],
        value_vars = ["items_ord_variance_abs", "sales_variance_abs", "avg_rsp_variance_abs"],
        var_name = "metric")

#create a columns to hold the position of each subplot 
df2["row"] = 1
df2["col"] = 1
df2.loc[df2["metric"] == "items_ord_variance_abs", "col"] = 2
df2.loc[df2["metric"] == "avg_rsp_variance_abs", "col"] = 3

#now use make_subplots to create the plot
fig = make_subplots(cols = 3, rows = 1,
                subplot_titles= ["Sales Variance", "Items Ord Variance", "Avg RSP Variance"])

#loop over each metric in the dataframe and create a seprate graph within the subplot
for metric in df2["metric"].unique():
    df_plot = df2.loc[df2["metric"] == metric].copy()
    
    fig.add_trace(go.Bar(x = df_plot["value"], 
                        y = df_plot["category_name"],
                        orientation = "h",
                        name = df_plot["metric"].tolist()[0]),
                        row = df_plot["row"].tolist()[0], #apply the row position we created above
                        col = df_plot["col"].tolist()[0]) #apply the column position we created above

fig.update_layout(plot_bgcolor = "white",
                    font = dict(color = "#909497"),
                    title = dict(text = "Year on Year Sales Variance by Category for Pakistan Ecommerce Stores"),
                    yaxis = dict(title = "Product Category", linecolor = "white",
                                categoryorder = "array", categoryarray = CATEGORY_ORDER),
                    xaxis = dict(tickprefix = "&#8377;"),
                    xaxis2 = dict(tickformat = ","),
                    xaxis3 = dict(tickprefix = "&#8377;"))

fig.update_xaxes(title = "", linecolor = "#909497")


#add a vertical line at x = 0 to act as x-axis
fig.add_vline(x = 0, line_color = "#909497", line_width = 1)

fig.show()

##########
# Step 5 #
##########

#transform the df dataframe again and this time include the absolute variance in sales and % variance in sales, 
#items ordered and avg rsp 
df3 = df.melt(id_vars = ["category_name"],
        value_vars = ["sales_variance_abs", "items_ord_variance_%", "sales_variance_%", "avg_rsp_variance_%"],
        var_name = "metric")

#create columns to hold the position of each metric in the subplot
df3["row"] = 1
df3["col"] = 1
df3.loc[df3["metric"] == "sales_variance_%", "col"] = 2
df3.loc[df3["metric"] == "items_ord_variance_%", "col"] = 3
df3.loc[df3["metric"] == "avg_rsp_variance_%", "col"] = 4

#create the dataframe that contains the subplot titles and x-axis positions
df_subplot_titles = pd.DataFrame({
    "titles": ["Sales Variance (Abs)", "Sales Variance (%)", "Items Ord Variance (%)", "Avg RSP Variance (%)"],
    "column": ["x1", "x2", "x3", "x4"],
    "x": [-4000000,-1,-1,-1]
})

#create the plot
fig = make_subplots(cols = 4, rows = 1,
                    shared_yaxes = True) #set the subplots to share the y-axis so it only appears once

for metric in df3["metric"].unique():
    df_plot = df3.loc[df3["metric"] == metric].copy()
    
    fig.add_trace(go.Bar(x = df_plot["value"], 
                        y = df_plot["category_name"],
                        orientation = "h",

                        name = df_plot["metric"].tolist()[0]),
                        row = df_plot["row"].tolist()[0],
                        col = df_plot["col"].tolist()[0])

fig.update_layout(plot_bgcolor = "white",
                    font = dict(color = "#909497"),
                    title = dict(text = "Year on Year Sales Variance by Category for Pakistan Ecommerce Stores"),
                    yaxis = dict(title = "Product Category", tickformat = ",", linecolor = "white",
                                categoryorder = "array", categoryarray = CATEGORY_ORDER),
                    xaxis = dict(tickprefix = "&#8377;", range = [-4000000,10000000]),
                    xaxis2 = dict(tickformat = "%", range = [-1,4]),
                    xaxis3 = dict(tickformat = "%", range = [-1,4]),
                    xaxis4 = dict(tickformat = "%", range = [-1,4]),
                    showlegend = False)

fig.update_xaxes(title = "", linecolor = "#909497", side = "top") #set the x-axes to appear at the top of the charts


#add a vertical line at x = 0 to act as x-axis
fig.add_vline(x = 0, line_color = "#909497", line_width = 1)

# add subplot titles manually
for title in df_subplot_titles["titles"].tolist():
    df_text = df_subplot_titles.loc[df_subplot_titles["titles"] == title]
    fig.add_annotation(text = title,
                    xref = df_text["column"].tolist()[0],
                    yref = "paper",
                    x = df_text["x"].tolist()[0],
                    y = 1.08,
                    showarrow = False,
                    align = "left",
                    xanchor = "left",
                    font = dict(size = 14)
                    )

fig.show()


##########
# Step 6 #
##########

#create a column for color
df3["color"] = "#BDC3C7"
df3.loc[df3["category_name"] == "Mobiles & Tablets", "color"] = "#2471A3"

#create a column for the widths of each bar plot
df3["width"] = 0.15 
df3.loc[df3["metric"] == "sales_variance_abs", "width"] = 0.8

fig = make_subplots(cols = 4, rows = 1,
                    shared_yaxes = True,
                    column_widths = [0.4, 0.2, 0.2, 0.2]) #set the widths of each graph in the subplot giving more prominence to the first one

#create two different data frames in the for loop one for the Mobile & Tablets category only and another without it
for metric in df3["metric"].unique():
    df_plot_non_mobile_tablet = df3.loc[(df3["metric"] == metric) & (df3["category_name"] != "Mobiles & Tablets")].copy()
    df_plot_mobile_tablet  = df3.loc[(df3["metric"] == metric) & (df3["category_name"] == "Mobiles & Tablets")].copy()
    fig.add_trace(go.Bar(x = df_plot_non_mobile_tablet["value"], 
                        y = df_plot_non_mobile_tablet["category_name"],
                        width = df_plot_non_mobile_tablet["width"],
                        orientation = "h",
                        marker = dict(color = df_plot_non_mobile_tablet["color"].tolist()[0])),
                        row = df_plot_non_mobile_tablet["row"].tolist()[0],
                        col = df_plot_non_mobile_tablet["col"].tolist()[0])

    #add a second trace in to deal with different colored category
    fig.add_trace(go.Bar(x = df_plot_mobile_tablet["value"], 
                        y = df_plot_mobile_tablet["category_name"],
                        width = df_plot_mobile_tablet["width"],
                        orientation = "h",
                        marker = dict(color = df_plot_mobile_tablet["color"].tolist()[0])),
                        row = df_plot_mobile_tablet["row"].tolist()[0],
                        col = df_plot_mobile_tablet["col"].tolist()[0])

fig.update_layout(plot_bgcolor = "white",
                    font = dict(color = "#909497"),
                    title = dict(text = "Year on Year Change in Sales by Category for Pakistan Ecommerce Stores"),
                    yaxis = dict(title = "Product Category", tickformat = ",", linecolor = "white",
                                categoryorder = "array", categoryarray = CATEGORY_ORDER),
                    xaxis = dict(tickprefix = "&#8377;", range = [-4000000,10000000]),
                    xaxis2 = dict(tickformat = "%",  range = [-1,4]),
                    xaxis3 = dict(tickformat = "%",  range = [-1,4]),
                    xaxis4 = dict(tickformat = "%",  range = [-1,4]),
                    showlegend = False)

fig.update_xaxes(title = "",  linecolor = "#909497", side = "top")

#add a vertical line at x = 0 to act as x-axis
fig.add_vline(x = 0, line_color = "#909497", line_width = 1)

# add subplot titles manually
for title in df_subplot_titles["titles"].tolist():
    df_text = df_subplot_titles.loc[df_subplot_titles["titles"] == title]
    fig.add_annotation(text = title,
                    xref = df_text["column"].tolist()[0],
                    yref = "paper",
                    x = df_text["x"].tolist()[0],
                    y = 1.08,
                    showarrow = False,
                    align = "left",
                    xanchor = "left",
                    font = dict(size = 14)
                    )

fig.show()


##########
# Step 7 #
##########


import numpy as np

# create the labels for the y-axis
df_xaxis_labels = pd.DataFrame({
    "category_name": df["category_name"].tolist(),
    "yref": np.repeat("y", len(df["category_name"]))
})

#set the color of the y-axis labels
df_xaxis_labels["color"] = "#909497"
df_xaxis_labels.loc[df_xaxis_labels["category_name"] == "Mobiles & Tablets", "color"] = "#2471A3"

#create the variable names needed for the hover info
df3["hover_info_text"] = "Sales Variance (Abs)"
df3.loc[df3["metric"] == "qty_ordered_yoy_%", "hover_info_text"] = "Items Ord Variance (%)"
df3.loc[df3["metric"] == "grand_total_yoy_%", "hover_info_text"] = "Sales Variance (%)"
df3.loc[df3["metric"] == "average_selling_price_yoy_%", "hover_info_text"] = "Avg RSP Variance (%)"

#create the size of the item range information for mobiles and tablet category
df_price_commentary = df_raw.loc[df_raw["category_name_1"] == "Mobiles & Tablets", ["item_id", "price", "season_ind"]].copy()

#how many mobiles and tables in each season all together
df_price_commentary_range = df_price_commentary.groupby("season_ind").agg(range_size = ("item_id", "nunique")).reset_index()

#how many mobiles and tables in each season over 40,000 rupees
df_price_commentary_high_price_point = df_price_commentary.loc[df_price_commentary["price"] >= 40000, ["season_ind", "item_id"]].groupby("season_ind").agg(range_size = ("item_id", "nunique")).reset_index()

#create the range size variables to be used in the commentary
MT_RANGE_LY = int(round(df_price_commentary_range.loc[df_price_commentary_range["season_ind"] == "Last Year", "range_size"].tolist()[0]/1000, 0))
MT_RANGE_TY = round(df_price_commentary_range.loc[df_price_commentary_range["season_ind"] == "This Year", "range_size"].tolist()[0]/1000, 1)
MT_RANGE_PERC_HIGH_PRICE_POINT_LY = df_price_commentary_high_price_point.loc[df_price_commentary_high_price_point["season_ind"] == "Last Year", "range_size"].tolist()[0]/1000 / MT_RANGE_LY
MT_RANGE_PERC_HIGH_PRICE_POINT_TY = df_price_commentary_high_price_point.loc[df_price_commentary_high_price_point["season_ind"] == "This Year", "range_size"].tolist()[0]/1000 / MT_RANGE_TY

#create the plot
fig = make_subplots(cols = 4, rows = 1,
                    shared_yaxes = True,
                    column_widths = [0.4, 0.2, 0.2, 0.2])

for metric in df3["metric"].unique():
    df_plot_non_mobile_tablet = df3.loc[(df3["metric"] == metric) & (df3["category_name"] != "Mobiles & Tablets")].copy()
    df_plot_mobile_tablet  = df3.loc[(df3["metric"] == metric) & (df3["category_name"] == "Mobiles & Tablets")].copy()
    fig.add_trace(go.Bar(x = df_plot_non_mobile_tablet["value"], 
                        y = df_plot_non_mobile_tablet["category_name"],
                        width = df_plot_non_mobile_tablet["width"],
                        orientation = "h",
                        marker = dict(color = df_plot_non_mobile_tablet["color"].tolist()[0]),
                        text = df_plot_non_mobile_tablet["hover_info_text"],
                        hovertemplate = 
                        "Category: %{y}<br>" +
                        "%{text}: %{x}<extra></extra>"),
                        row = df_plot_non_mobile_tablet["row"].tolist()[0],
                        col = df_plot_non_mobile_tablet["col"].tolist()[0])

    #add a second trace in to deal with different colored category
    fig.add_trace(go.Bar(x = df_plot_mobile_tablet["value"], 
                        y = df_plot_mobile_tablet["category_name"],
                        width = df_plot_mobile_tablet["width"],
                        orientation = "h",
                        marker = dict(color = df_plot_mobile_tablet["color"].tolist()[0]),
                        text = df_plot_mobile_tablet["hover_info_text"],
                        hovertemplate = 
                        "Category: %{y}<br>" +
                        "%{text}: %{x}<extra></extra>"),
                        row = df_plot_mobile_tablet["row"].tolist()[0],
                        col = df_plot_mobile_tablet["col"].tolist()[0])

fig.update_layout(plot_bgcolor = "white",
                    font = dict(color = "#909497"),
                    yaxis = dict(title = "Category",
                                categoryorder = "array", categoryarray = CATEGORY_ORDER, visible = False),
                    xaxis = dict(tickprefix = "&#8377;", range = [-4000000,10000000]),
                    xaxis2 = dict(tickformat = "%",  range = [-1,4]),
                    xaxis3 = dict(tickformat = "%",  range = [-1,4]),
                    xaxis4 = dict(tickformat = "%",  range = [-1,4]),
                    showlegend = False,
                    margin = dict(l = 120, t = 140))

fig.update_xaxes(title = "",  linecolor = "#909497", side = "top")
fig.update_yaxes(categoryorder = "array", categoryarray = CATEGORY_ORDER)

fig.add_vline(x = 0, line_color = "#909497", line_width = 1)

# add subplot titles manually
for title in df_subplot_titles["titles"].tolist():
    df_text = df_subplot_titles.loc[df_subplot_titles["titles"] == title].copy()
    fig.add_annotation(text = title,
                    xref = df_text["column"].tolist()[0],
                    yref = "paper",
                    x = df_text["x"].tolist()[0],
                    y = 1.1,
                    showarrow = False,
                    align = "left",
                    xanchor = "left",
                    font = dict(size = 13, color = "#242526")
                    )

# add y axis labels manually
for label in df_xaxis_labels["category_name"].tolist():
    df_xaxis = df_xaxis_labels.loc[df_xaxis_labels["category_name"] == label].copy()
    fig.add_annotation(text = label,
                    xref = "paper",
                    yref = df_xaxis["yref"].tolist()[0],
                    x = 0,
                    y = label,
                    showarrow = False,
                    align = "right",
                    xanchor = "right",
                    font = dict(size = 11, color = df_xaxis["color"].tolist()[0])
                    )

# add y axis title
fig.add_annotation(text = "Product Category",
                    xref = "paper",
                    yref = "paper",
                    x = -0.095,
                    y = 1.06,
                    showarrow = False,
                    align = "left",
                    xanchor = "left",
                    font = dict(size = 11)
                    )

# add title manually
fig.add_annotation(text = '<span style="color:#2471A3">Mobiles & Tablets</span> Experienced Largest Sales Growth...',
                xref = "paper",
                yref = "paper",
                x = -0.095,
                y = 1.37,
                showarrow = False,
                align = "left",
                xanchor = "left",
                font = dict(size = 18, color = "#242526")
                )

# add sub title 
fig.add_annotation(text = "E-commerce data from various merchants in Pakistan",
                    xref = "paper",
                    yref = "paper",
                    x = -0.095,
                    y = 1.315,
                    showarrow = False,
                    align = "left",
                    xanchor = "left",
                    font = dict(size = 11)
                    )

#add in commentary
fig.add_annotation(text = '...year-on-year in Q3 2018 at <span style="color:#2471A3">+&#8377;9.5M</span> (<span style="color:#2471A3">+28%</span>). The entire growth was driven by a significant increase in the avg RSP YoY (<span style="color:#2471A3">+356%</span>). ' +
                        'Between Q3 2017 and 2018, two notable changes in the <span style="color:#2471A3">Mobiles & Tablets</span> category <br>impacted the avg RSP. The first one being a severe reduction in the range of products sold, dropping from 6k to 2.2k. The second notable change was a significant move into higher price point items with 9.2% of <br>products sold above the &#8377;40k price point in Q3 2018 compared to only 0.4% in Q3 2017.',
                    xref = "paper",
                    yref = "paper",
                    x = -0.095,
                    y = 1.255,
                    showarrow = False,
                    align = "left",
                    xanchor = "left",
                    font = dict(size = 13, color = "#242526"))



#add author of the graph
fig.add_annotation(text = "Author: Tom Price",
                    xref = "paper",
                    yref = "paper",
                    x = 1.005,
                    y = -0.11,
                    showarrow = False,
                    font = dict(size = 11),
                    align = "right",
                    xanchor = "right")

#add the data source of the graph
fig.add_annotation(text = "Data Source: kaggle.com",
                    xref = "paper",
                    yref = "paper",
                    x = -0.095,
                    y = -0.11,
                    showarrow = False,
                    font = dict(size = 11),
                    align = "left",
                    xanchor = "left")


fig.show()


