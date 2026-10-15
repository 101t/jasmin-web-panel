(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var MTROUTER_DICT = {}, SMPPCCM_DICT = {}, FILTERS_DICT = {};
    var COLUMNS = 7;

    var chips = function(items, css) {
        return $.map(items || [], function(item){
            return '<span class="badge ' + css + ' mr-1 text-wrap text-left">' + escapeHtml(item) + '</span>';
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
                var datalist = data["mtrouters"];
                MTROUTER_DICT = {};
                var output = $.map(datalist, function(val, i){
                    MTROUTER_DICT[i+1] = val;
                    return '<tr>' +
                        '<td>' + (i+1) + '</td>' +
                        '<td>' + escapeHtml(val.type) + '</td>' +
                        '<td>' + escapeHtml(val.order) + '</td>' +
                        '<td>' + escapeHtml(val.rate) + '</td>' +
                        '<td>' + chips(val.connectors, 'badge-primary') + '</td>' +
                        '<td>' + (val.filters && val.filters.length ? chips(val.filters, 'badge-light border') : '<span class="text-muted">—</span>') + '</td>' +
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

    var loadOptions = function(url, key, select, toOption, emptyLabel){
        $.ajax({
            url: url,
            type: "POST",
            data: {csrfmiddlewaretoken: csrfmiddlewaretoken, s: "list"},
            dataType: "json",
            success: function(data){
                var html = $.map(data[key], toOption);
                $(add_modal_form + " select[name=" + select + "]").html(
                    html.length ? html.join('') : '<option value="" disabled>' + escapeHtml(emptyLabel) + '</option>');
            },
            error: showAjaxError
        });
    };

    // A route type decides how many connectors it takes and whether it has an order and filters.
    var applyRouteType = function(){
        var type = $(add_modal_form + " select[name=type]").val();
        var isDefault = type === "DefaultRoute";
        var many = type === "RandomRoundrobinMTRoute" || type === "FailoverMTRoute";
        var $connectors = $(add_modal_form + " select[name=smppconnectors]");
        $connectors.prop("multiple", many).attr("size", many ? 5 : null);
        $("#connectors_hint").text(many ? main_trans.manyConnectors : main_trans.oneConnector);
        $(add_modal_form + " .route-order").toggle(!isDefault);
        $(add_modal_form + " .route-filters").toggle(!isDefault);
        $(add_modal_form + " input[name=order]").prop("required", !isDefault);
    };
    $(add_modal_form + " select[name=type]").on("change", applyRouteType);

    window.collection_manage = function(cmd, index){
        index = index || -1;
        if (cmd == "add") {
            $(add_modal_form)[0].reset();
            applyRouteType();
            showThisBox(variant_boxes, add_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "delete") {
            var route = MTROUTER_DICT[index];
            confirmAction(function(){
                postAction(local_path + 'manage/', {s: cmd, order: route.order}, collectionlist_check);
            });
        } else if (cmd == "smppccm") {
            loadOptions(main_trans.url2smppccm, "connectors", "smppconnectors", function(val, i){
                SMPPCCM_DICT[i+1] = val;
                return '<option value="' + escapeHtml(val.cid) + '">' + escapeHtml(val.cid) + ' (' + escapeHtml(val.status) + ')</option>';
            }, main_trans.noConnectors);
        } else if (cmd == "filters") {
            loadOptions(main_trans.url2filters, "filters", "filters", function(val, i){
                FILTERS_DICT[i+1] = val;
                // Jasmin refuses MO-only filters (ConnectorFilter) on MT routes.
                if ((val.routes || '').split(' ').indexOf('MT') === -1) return null;
                return '<option value="' + escapeHtml(val.fid) + '">' + escapeHtml(val.fid + ' — ' + val.description) + '</option>';
            }, main_trans.noFilters);
        }
    };
    collection_manage("smppccm");
    collection_manage("filters");
    $("#add_new_obj").on('click', function(e){collection_manage('add');});
    $(add_modal_form).on("submit", function(e){
        e.preventDefault();
        submitAjaxForm(this, collectionlist_check);
    });
    $("li.nav-item.mtrouter-menu").addClass("active");
})(jQuery);
