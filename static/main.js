$(document).ready(function () {
    $('#userName').keyup(function(){
        var data = $("#regForm").serialize()
        $.ajax({
            method: "POST",
            url: "/username",
            data: data
        })
        .done(function(res){
            $('#usernameMsg').html(res)
        })
    })
});