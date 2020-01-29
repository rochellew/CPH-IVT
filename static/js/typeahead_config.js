var TypeaheadSetup = (function() {

    function setup(config)  {
        function get_tokens(datum) {
            return datum.tokens;
        }

        function get_id(datum) {
            return datum.id;
        }

        function make_header(title) {
            return "<h3 class='suggestion-category'>" + title + "</h3>";
        }

        function render_suggestion(context) {
            return "<div>" +
                context.name +
                " <small>" +
                context.state +
                "</small></div>";
        }

        const county_source = new Bloodhound({
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            datumTokenizer: get_tokens,
            identify: get_id,
            prefetch: config.prefetch.county,
            remote: {
                url: config.remote.county,
                wildcard: config.remote.wildcard
            }
        });

        const state_source = new Bloodhound({
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            datumTokenizer: Bloodhound.tokenizers.whitespace,
            prefetch: config.prefetch.state,
            remote: {
                url: config.remote.state,
                wildcard: config.remote.wildcard
            }
        });

        $("#search_box").typeahead(
            {
                highlight: true,
                autoselect: true,
                minLength: 2
            },
            {
                name: "states",
                source: state_source,
                limit: 5,
                templates: {
                    header: make_header("States")
                }
            },
            {
                name: "counties",
                source: county_source,
                displayKey: "value",
                limit: 10,
                templates: {
                    header: make_header("Counties"),
                    suggestion: render_suggestion
                }
            }
        );
    }

    var exports = {
        init: setup
    };

    return exports;
})();
