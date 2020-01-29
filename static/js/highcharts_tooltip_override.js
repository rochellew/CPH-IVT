/* Extension to HighCharts that forces tooltips to behave differently by overriding methods on the
Tooltip class. The 'hide' method is replaced with a no-op procedure, so that the tooltip is
never hidden from the chart. The 'refresh' method is overriden to include a conditional check
for whether a point is selected before calling the original 'refresh' method. This stops the
content of the tooltip from being updated if a point is currently selected.

To use this, the file simply has to be sourced into the HTML *after* the Highcharts library
(and preferrably before our other customizations, but not necessarily).

Also, point selection *must* be enabled for the refresh-blocking function to work (the always
    show feature should work either way).

    Resources:
    + https://ahumbleopinion.com/customizing-highcharts-tooltip-visibility/
    + https://www.highcharts.com/docs/extending-highcharts/extending-highcharts

Created 2019-03-19 by Matthew Seiler
*/
(function(H) {
    // whether any point is currently in the 'selected' state
    // used to track whether we should allow the tooltip to update
    var pointSelected = false;
    // the last point that was used to update the tooltip
    // exporting re-renders the chart from scratch, so we need to know a little bit about the state
    // of the chart in order to add a psuedo-tooltip to the export.
    var lastPoint;

    // receive an event when a point is selected. The logic here looks strange because of the
    // case where you select a new point while another one is already selected; this function
    // will fire but tooltip refresh would be blocked because pointSelected would remain true.
    // So we detect that case, switch off pointSelected, fire refresh 'manually', then switch
    // pointSelected back on.
    H.addEvent(H.Point.prototype, 'select', function(ev) {
        // make sure the tooltip is updates with the selected point even if another point was
        // already selected!
        if (pointSelected) {
            pointSelected = false;
            this.series.chart.tooltip.refresh(ev.target);
        }
        // indicate that some point is in the selected state
        pointSelected = true;
    });

    // receieve an event when a point is *de*selected
    H.addEvent(H.Point.prototype, 'unselect', function(ev) {
        // record that there is no longer a point selected
        pointSelected = false;
    });

    // stop the tooltip from hiding by overriding the "hide" method
    H.wrap(H.Tooltip.prototype, 'hide', function(original) {
        // do nothing
    });

    // override the tooltip refresh method to prevent updating if a point is selected
    H.wrap(H.Tooltip.prototype, 'refresh', function(original, point) {
        if (!pointSelected) {
            // Template from here:
            // https://www.highcharts.com/docs/extending-highcharts/extending-highcharts
            // This calls the original refresh method with some JavaScript magic that
            // + passes any arguments passed to this function, minus the first one
            // + sets the context of the called function to the same as right here ('this')
            original.apply(this, Array.prototype.slice.call(arguments, 1));
            // track the point that was used to update the tooltip
            lastPoint = point;
        }
    });

    var exportWrapper = function(original, exportOptions, chartOptions) {
        var loadEventOptions = {
            chart: {
                events: {
                    load: function() {
                        // when the chart loads for rendering, force the tooltip to be populated
                        // with the data from the last point that was used prior to rendering
                        if (lastPoint != undefined) {
                            // need to set pointSelected to false (even if a point *is* selected)
                            // so that the refresh will work, since this will call wrapped versiin
                            oldPointSelected = pointSelected;
                            pointSelected = false;

                            this.tooltip.refresh(lastPoint);

                            // restore this to whatever it was before
                            pointSelected = oldPointSelected;
                        }
                    }
                }
            }
        };
        // call the original export function
        original.apply(this, [exportOptions, H.merge(chartOptions, loadEventOptions)]);
    };

    // wrap the exportChart method to intercept exports and add to the chart configuration
    // used to render the exported image before calling the original exportChart function
    H.wrap(H.Chart.prototype, "exportChart", exportWrapper); // from export.js
    //
    H.wrap(H.Chart.prototype, "exportChartLocal", exportWrapper); // fromoffline-exporting.js

}(Highcharts));