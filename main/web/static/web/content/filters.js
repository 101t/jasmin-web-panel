(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var FILTERS_DICT = {};
    var COLUMNS = 6;
    var routeBadges = function(routes){
        return $.map((routes || '').split(' '), function(route){
            return route ? '<span class="badge badge-light border mr-1">' + escapeHtml(route) + '</span>' : null;
        }).join('');
    };
    var collectionlist_check = function(){
        tableLoading("#collectionlist", COLUMNS);
        $.ajax({
            url: local_path + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list",
            },
            dataType: "json",
            success: function(data){
                var datalist = data["filters"];
                FILTERS_DICT = {};
                var output = $.map(datalist, function(val, i){
                    FILTERS_DICT[i+1] = val;
                    return '<tr>' +
                        '<td>' + (i+1) + '</td>' +
                        '<td>' + escapeHtml(val.fid) + '</td>' +
                        '<td>' + escapeHtml(val.type) + '</td>' +
                        '<td>' + routeBadges(val.routes) + '</td>' +
                        '<td><code>' + escapeHtml(val.description) + '</code></td>' +
                        '<td class="text-center" style="padding-top:4px;padding-bottom:4px;"><div class="btn-group btn-group-sm">' +
                            '<button type="button" class="btn btn-light" title="' + escapeHtml(main_trans.delete) + '" aria-label="' + escapeHtml(main_trans.delete) + '" onclick="return collection_manage(\'delete\', ' + (i+1) + ');"><i class="fas fa-trash"></i></button>' +
                        '</div></td>' +
                    '</tr>';
                });
                $("#collectionlist").html(datalist.length > 0 ? output.join('') : $(".isEmpty").html());
            },
            error: function(jqXHR){ tableError("#collectionlist", COLUMNS, jqXHR, collectionlist_check); }
        });
    };
    collectionlist_check();
    window.collection_manage = function(cmd, index){
        index = index || -1;
        if (cmd == "add") {
            $(add_modal_form)[0].reset();
            $("#filter_type").trigger("change");
            showThisBox(variant_boxes, add_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "delete") {
            var filter = FILTERS_DICT[index];
            confirmAction(function(){
                postAction(local_path + 'manage/', {s: cmd, fid: filter.fid}, collectionlist_check);
            });
        }
    };
    $("#add_new_obj").on('click', function(e){collection_manage('add');});
    $(add_modal_form).on("submit", function(e){
        e.preventDefault();
        submitAjaxForm(this, collectionlist_check);
    });
    $("li.nav-item.filters-menu").addClass("active");

    // One parameter per filter type: [jcli key, placeholder, help, routes it can be used in].
    // The routes mirror Jasmin's MOFILTERS / MTFILTERS lists.
    var FILTER_PARAMETERS = {
        connectorfilter: ["cid", "smpp-01", "of the connector to match", "MO"],
        userfilter: ["uid", "bobo", "of the user to match", "MT"],
        groupfilter: ["gid", "partners", "of the group to match", "MT"],
        sourceaddrfilter: ["source_addr", "^20\\d+", "Regular expression to match source address", "MO MT"],
        destinationaddrfilter: ["destination_addr", "^85111$", "Regular expression to match destination address", "MO MT"],
        shortmessagefilter: ["short_message", "^hello.*$", "Regular expression to match message content", "MO MT"],
        dateintervalfilter: ["dateInterval", "2014-09-18;2014-09-28", "Two dates separated by ; (date format is YYYY-MM-DD)", "MO MT"],
        timeintervalfilter: ["timeInterval", "08:00:00;18:00:00", "Two timestamps separated by ; (timestamp format is HH:MM:SS)", "MO MT"],
        tagfilter: ["tag", "32401", "numeric tag to match in message", "MO MT"],
        evalpyfilter: ["pyCode", "/root/thirdparty.py", "Path to a python script", "MO MT"]
    };
    $("#filter_type").on("change", function(e){
        var val = $(this).val();
        var spec = FILTER_PARAMETERS[val];
        if (!spec) {
            $("#filter_routes").hide();
            $("#filter_routes_inputs").html('');
            $("#filter_route_hint").html(routeBadges("MO MT"));
            return;
        }
        var $input = $('<input type="text" name="parameter" class="form-control" required>').attr('placeholder', spec[1]);
        var $help = $('<span class="text-muted"></span>').append($('<b></b>').text(spec[0])).append(document.createTextNode(' ' + spec[2]));
        if (val === "evalpyfilter") {
            $help.append(document.createTextNode(' ('))
                .append($('<a target="_blank" rel="noopener"></a>').attr('href', 'https://docs.jasminsms.com/en/latest/management/jcli/modules.html#external-buslogig-filters').text('External business logic'))
                .append(document.createTextNode(')'));
        }
        $("#filter_routes_inputs").empty().append($input).append($help);
        $("#filter_route_hint").html(routeBadges(spec[3]));
        $("#filter_routes").show();
    }).trigger("change");
})(jQuery);
