.. keywords
   winds, movers, GFS, NAM, meteorological

The Mover data availability section at the top of this form provides information on the time range of the input file. If the mover is being shifted into the model timezone, that information will also be displayed.

The **Name** by default is set from the uploaded file name. It can be edited for clarity.

If checked, **Adjust to Model Timezone** will shift the time series from the original timezone to the model timezone. The new start and end dates for the shifted time series will display in the Mover Data Availability box at the top. Changes to the **Model Timezone** in this form will also be applied to the model (by default it will match the time zone specified in the **Model Settings**). 

The **Active Range** option can be used to limit the time interval in which the Mover is applied to the particles. The default is **Infinite** in which case the model will apply this Mover at all times and errors will occur if the model run time is outside the interval of available data. A second option is to choose **Set to Start/End Times**. In this case, the Mover will be applied only while within the data range of the input file and will be inactive at other times. 

The **Scale Value** applies a multipicative scale to all the velocity values used by the current mover. Note, the underlying data is unchanged and hence the vector displays in the Map View will not reflect this scaling. Scaling is uniform across the grid.

The **Extrapolate** option allows the current mover to operate outside the time span of the underlying data. For example, at times before the **Start Time** the initial velocity values will be used, At times after the **End Time**, the final velocity value will be used.