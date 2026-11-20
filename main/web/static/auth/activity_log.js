(function($){
    var view_modal_form = "#view_modal_form";
    var esc = function(value){
        if (typeof window.escapeHtml === "function") {
            return window.escapeHtml(value);
        }
        if (value === null || value === undefined) return "";
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    };
    var slug2title = function(string){
        return toTitleCase(String(string).replace(/_/g, " "));
    };
    window.collection_manage = function(cmd, index){
        if (cmd == "view") {
            var data = $(index).next("input[name=data]").val();
            data = JSON.parse(data);
            var table0 = `
                <tr>
                    <th>${esc(main_trans.ipaddress)}</th>
                    <td>${esc(data.ip)}</td>
                </tr>
                <tr>
                    <th>${esc(main_trans.method)}</th>
                    <td>${esc(data.method)}</td>
                </tr>
                <tr>
                    <th>${esc(main_trans.service)}</th>
                    <td>${esc(data.service)}</td>
                </tr>
                <tr>
                    <th>${esc(main_trans.path)}</th>
                    <td>${esc(data.path)}</td>
                </tr>
            `;
            var table1 = $.map(data.params || {}, function(val, i){
                return `<tr>
                    <td>${esc(slug2title(i))}</td>
                    <td><strong>${esc(i)}</strong></td>
                    <td>${esc(val)}</td>
                </tr>`;
            });
            var table2 = $.map(data.user_agent || {}, function(val, i){
                var tds = "";
                if (i === "os") {
                    tds = `<th>OS</th><td>${esc(val)}</td>`;
                } else if (i === "ua_string") {
                    tds = `<th>User Agent</th><td>${esc(val)}</td>`;
                } else {
                    tds = `<th>${esc(slug2title(i))}</th><td>${esc(val)}</td>`;
                }
                return `<tr>${tds}</tr>`;
            });
            $(view_modal_form+" table:eq(0) tbody").html(table0);
            $(view_modal_form+" table:eq(1) tbody").html(table1);
            $(view_modal_form+" table:eq(2) tbody").html(table2);
            $("#collection_modal").modal("show");
        }
    };
})(jQuery);