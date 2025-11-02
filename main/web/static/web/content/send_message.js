(function($){
    var csrfmiddlewaretoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    
    // Fetch users from gateway
    function loadGatewayUsers() {
        $.ajax({
            url: window.location.pathname + 'manage/',
            type: "POST",
            data: {
                csrfmiddlewaretoken: csrfmiddlewaretoken,
                s: "list_users"
            },
            dataType: "json",
            success: function(data){
                if (data.users && data.users.length > 0) {
                    var options = '<option value="">Default (Environment Credentials)</option>';
                    data.users.forEach(function(user){
                        // Only show enabled users
                        if (user.status === 'enabled') {
                            options += '<option value="' + user.uid + '">' + 
                                      user.uid + ' (' + user.username + ')</option>';
                        }
                    });
                    $('#user_uid').html(options);
                } else {
                    $('#user_uid').html('<option value="">Default (Environment Credentials)</option>');
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                console.error('Failed to load gateway users:', textStatus);
                $('#user_uid').html('<option value="">Default (Environment Credentials)</option>');
            }
        });
    }
    
    // Load users on page load
    loadGatewayUsers();
    
    $("li.nav-item.send-sms-menu").addClass("active");
})(jQuery);