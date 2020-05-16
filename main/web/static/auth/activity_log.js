(function($){
    var view_modal_form = "#view_modal_form";
    var slug2title = function(string){
        return toTitleCase(string.replace("_", " "));
    }
    window.collection_manage = function(cmd, index){
        if (cmd == "view") {
            var data = $(index).next("input[name=data]").val();
            data = JSON.parse(data);
            //console.log(data);
            var table0 = `
                <tr>
                    <th>${main_trans.ipaddress}</th>
                    <td>${data.ip}</td>
                </tr>
                <tr>
                    <th>${main_trans.method}</th>
                    <td>${data.method}</td>
                </tr>
                <tr>
                    <th>${main_trans.service}</th>
                    <td>${data.service}</td>
                </tr>
                <tr>
                    <th>${main_trans.path}</th>
                    <td>${data.path}</td>
                </tr>
            `;
            var table1 = $.map(data.params, function(val, i){
                return `<tr>
                    <td>${slug2title(i)}</td>
                    <td><strong>${i}</strong></td>
                    <td>${val}</td>
                </tr>`;
            })
            var table2 = $.map(data.user_agent, function(val, i){
                var tds = "";
                if (["os", "ua_string"].indexOf(i) > -1) {
                    if (i === "os") {
                        tds = `
                            <th>OS</th>
                            <td>${val}</td>
                        `;
                    } else if (i === "ua_string") {
                        tds = `
                            <th>User Agent</th>
                            <td>${val}</td>
                        `;
                    }
                } else {
                    tds = `
                        <th>${slug2title(i)}</th>
                        <td>${val}</td>
                    `;
                }
                return `<tr>
                    ${tds}
                </tr>`;
            })
            $(view_modal_form+" table:eq(0) tbody").html(table0);
            $(view_modal_form+" table:eq(1) tbody").html(table1);
            $(view_modal_form+" table:eq(2) tbody").html(table2);
            $("#collection_modal").modal("show");
        }
    }
})(jQuery);