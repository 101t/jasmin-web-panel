(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var USERS_DICT = {}, GROUPS_DICT = {};
    var AUTHORIZATIONS = ["http_send", "http_balance", "http_rate", "http_bulk", "smpps_send", "http_long_content",
        "dlr_level", "http_dlr_method", "src_addr", "priority", "validity_period", "schedule_delivery_time", "hex_content"];
    var COLUMNS = 8;

    var statusBadge = function(status) {
        return status === "enabled"
            ? '<span class="badge badge-success">' + escapeHtml(main_trans.enabled) + '</span>'
            : '<span class="badge badge-secondary">' + escapeHtml(main_trans.disabled) + '</span>';
    };
    var actionButton = function(cmd, index, icon, title) {
        return '<button type="button" class="btn btn-light" title="' + escapeHtml(title) + '" aria-label="' + escapeHtml(title) +
            '" onclick="return collection_manage(\'' + cmd + '\', ' + index + ');"><i class="fas ' + icon + '"></i></button>';
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
                var datalist = data["users"];
                USERS_DICT = {};
                var output = $.map(datalist, function(val, i){
                    var quota = (val.mt_messaging_cred || {}).quota || {};
                    USERS_DICT[i+1] = val;
                    return '<tr>' +
                        '<td>' + (i+1) + '</td>' +
                        '<td>' + escapeHtml(val.uid) + '</td>' +
                        '<td>' + escapeHtml(val.gid) + '</td>' +
                        '<td>' + escapeHtml(val.username) + '</td>' +
                        '<td class="text-center">' + statusBadge(val.status) + '</td>' +
                        '<td>' + escapeHtml(quota.balance) + '</td>' +
                        '<td>' + escapeHtml(quota.sms_count) + '</td>' +
                        '<td class="text-center" style="padding-top:4px;padding-bottom:4px;"><div class="btn-group btn-group-sm">' +
                            actionButton('service', i+1, 'fa-play-circle', main_trans.service) +
                            actionButton('edit', i+1, 'fa-edit', main_trans.edit) +
                            actionButton('delete', i+1, 'fa-trash', main_trans.delete) +
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
            showThisBox(variant_boxes, add_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "edit") {
            var data = USERS_DICT[index];
            var cred = data.mt_messaging_cred || {};
            var quota = cred.quota || {}, authorization = cred.authorization || {};
            var valuefilter = cred.valuefilter || {}, defaultvalue = cred.defaultvalue || {};
            var $form = $(edit_modal_form);
            $form.find("input[name=uid]").val(data.uid);
            $form.find("input[name=username]").val(data.username);
            // Jasmin never returns passwords: leave it empty, it is only sent when typed in.
            $form.find("input[name=password]").val('');
            $form.find("select[name=gid]").val(data.gid);
            $.each(["balance", "sms_count", "early_percent", "http_throughput", "smpps_throughput"], function(_, key){
                $form.find("input[name=" + key + "]").val(quota[key] !== undefined ? quota[key] : '');
            });
            $.each(AUTHORIZATIONS, function(_, key){
                var $box = $form.find("input[name=" + key + "]");
                $box.prop("checked", authorization[key] === "True");
                // Older gateways do not know every flag; do not offer what cannot be saved.
                $box.closest(".form-group").toggle(authorization[key] !== undefined);
            });
            $form.find("input[name=src_addr_f]").val(valuefilter.src_addr || '');
            $form.find("input[name=dst_addr_f]").val(valuefilter.dst_addr || '');
            $form.find("input[name=content_f]").val(valuefilter.content || '');
            $form.find("input[name=priority_f]").val(valuefilter.priority || '');
            $form.find("input[name=validity_period_f]").val(valuefilter.validity_period || '');
            $form.find("input[name=src_addr_d]").val(defaultvalue.src_addr === "None" ? '' : (defaultvalue.src_addr || ''));
            showThisBox(variant_boxes, edit_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "delete") {
            var user = USERS_DICT[index];
            confirmAction(function(){
                postAction(local_path + 'manage/', {s: cmd, uid: user.uid}, collectionlist_check);
            });
        } else if (cmd == "service") {
            var target = USERS_DICT[index];
            $(service_modal_form+" input[name=uid]").val(target.uid);
            $(service_modal_form+" select[name=s]").val(target.status === "enabled" ? "disable" : "enable");
            showThisBox(variant_boxes, service_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "groups") {
            $.ajax({
                url: main_trans.url2groups,
                type: "POST",
                data: {
                    csrfmiddlewaretoken: csrfmiddlewaretoken,
                    s: "list",
                },
                dataType: "json",
                success: function(data){
                    var datalist = data["groups"];
                    var html = $.map(datalist, function(val, i){
                        GROUPS_DICT[i+1] = val;
                        var label = val.name + (val.status === "disabled" ? " (" + main_trans.disabled + ")" : "");
                        return '<option value="' + escapeHtml(val.name) + '">' + escapeHtml(label) + '</option>';
                    });
                    if (!html.length) {
                        html = ['<option value="" disabled selected>' + escapeHtml(main_trans.nogroups) + '</option>'];
                    }
                    $(add_modal_form+" select[name=gid]").html(html.join(''));
                    $(edit_modal_form+" select[name=gid]").html(html.join(''));
                },
                error: showAjaxError
            });
        }
    };
    collection_manage("groups");
    $("#add_new_obj").on('click', function(e){collection_manage('add');});
    $(add_modal_form+","+edit_modal_form+","+service_modal_form).on("submit", function(e){
        e.preventDefault();
        submitAjaxForm(this, collectionlist_check);
    });

    // Toggle password visibility
    $(document).on('click', '.toggle-password', function(e){
        e.preventDefault();
        var $button = $(this);
        var $input = $button.closest('.input-group').find('.password-input');
        var $icon = $button.find('i');

        if ($input.attr('type') === 'password') {
            $input.attr('type', 'text');
            $icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            $input.attr('type', 'password');
            $icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });

    $("li.nav-item.users-menu").addClass("active");
})(jQuery);
