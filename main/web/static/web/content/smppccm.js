(function($){
    var local_path = window.location.pathname, csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    var add_modal_form = "#add_modal_form", edit_modal_form = "#edit_modal_form", service_modal_form = "#service_modal_form";
    var variant_boxes = [add_modal_form, edit_modal_form, service_modal_form];
    var SMPPCCM_DICT = {};
    var COLUMNS = 8;
    // Edit form fields, named like the jcli smppccm keys returned by "smppccm -s".
    var EDIT_FIELDS = ["cid", "logfile", "logrotate", "loglevel", "host", "port", "ssl", "username", "password", "bind",
        "bind_to", "trx_to", "res_to", "pdu_red_to", "con_loss_retry", "con_loss_delay", "con_fail_retry", "con_fail_delay",
        "src_addr", "src_ton", "src_npi", "dst_ton", "dst_npi", "bind_ton", "bind_npi", "validity", "priority",
        "requeue_delay", "addr_range", "systype", "dlr_expiry", "submit_throughput", "proto_id", "coding",
        "elink_interval", "def_msg_id", "ripf", "dlr_msgid"];

    var statusBadge = function(val) {
        var started = val.status === "started";
        var label = (started ? main_trans.started : main_trans.stopped) + (val.session && val.session !== "NONE" ? ' · ' + val.session : '');
        return '<span class="badge ' + (started ? 'badge-success' : 'badge-secondary') + '">' + escapeHtml(label) + '</span>';
    };
    var collectionlist_check = function() {
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
                var datalist = data["connectors"];
                SMPPCCM_DICT = {};
                var output = $.map(datalist, function(val, i){
                    SMPPCCM_DICT[i+1] = val;
                    var maskedPassword = val.password ? '•'.repeat(Math.min(val.password.length, 8)) : '';
                    var button = function(cmd, icon, title) {
                        return '<button type="button" class="btn btn-light" title="' + escapeHtml(title) + '" aria-label="' + escapeHtml(title) +
                            '" onclick="return collection_manage(\'' + cmd + '\', ' + (i+1) + ');"><i class="fas ' + icon + '"></i></button>';
                    };
                    return '<tr>' +
                        '<td>' + (i+1) + '</td>' +
                        '<td>' + escapeHtml(val.cid) + '</td>' +
                        '<td>' + escapeHtml(val.host) + '</td>' +
                        '<td>' + escapeHtml(val.port) + '</td>' +
                        '<td>' + escapeHtml(val.username) + '</td>' +
                        '<td><span class="password-masked" title="' + escapeHtml(main_trans.masked) + '">' + maskedPassword + '</span></td>' +
                        '<td class="text-center">' + statusBadge(val) + '</td>' +
                        '<td class="text-center" style="padding-top:4px;padding-bottom:4px;"><div class="btn-group btn-group-sm">' +
                            button('service', 'fa-play-circle', main_trans.service) +
                            button('edit', 'fa-edit', main_trans.edit) +
                            button('delete', 'fa-trash', main_trans.delete) +
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
            var data = SMPPCCM_DICT[index];
            var $form = $(edit_modal_form);
            // Only the fields changed here are sent: the backend compares with the running config.
            $.each(EDIT_FIELDS, function(_, key){
                $form.find("[name=" + key + "]").val(data[key] !== undefined ? data[key] : '');
            });
            showThisBox(variant_boxes, edit_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "service") {
            var target = SMPPCCM_DICT[index];
            $(service_modal_form+" input[name=cid]").val(target.cid);
            $(service_modal_form+" select[name=s]").val(target.status === "started" ? "restart" : "start");
            showThisBox(variant_boxes, service_modal_form);
            $("#collection_modal").modal("show");
        } else if (cmd == "delete") {
            var connector = SMPPCCM_DICT[index];
            confirmAction(function(){
                postAction(local_path + 'manage/', {s: cmd, cid: connector.cid}, collectionlist_check);
            });
        }
    };
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

    $("li.nav-item.smppccm-menu").addClass("active");
})(jQuery);
