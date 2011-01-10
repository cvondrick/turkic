var turkic_timeaccepted = (new Date()).getTime();

/* automatically load dependents */
(function() {
var scripts = document.getElementsByTagName("script");
var src = scripts[scripts.length-1].src;
var folder = src.substr(0, src.lastIndexOf('/'));
document.write('<script src="' + folder + '/jquery.js"></script>');
document.write('<script src="' + folder + '/jquery.cookie.js"></script>');
})();

function mturk_parameters()
{
    var retval = new Object();
    retval.action = "http://www.mturk.com/mturk/externalSubmit";
    retval

    if (window.location.href.indexOf("?") == -1)
    {
        retval.assignmentid = null;
        retval.hitid = null;
        retval.workerid = null;
        return retval;
    }

    var params = window.location.href.split("?")[1].split("&");

    for (var i in params)
    {
        var sp = params[i].split("=");
        if (sp.length <= 1)
        {
            continue;
        }
        var result = sp[1].split("#")[0];

        if (sp[0] == "assignmentId")
        {
            retval.assignmentid = result;
        }
        else if (sp[0] == "hitId")
        {
            retval.hitid = result;
        }
        else if (sp[0] == "workerId")
        {
            retval.workerid = result;
        }
        else if (sp[0] == "turkSubmitTo")
        {
            retval.action = decodeURIComponent(result) +
                "/mturk/externalSubmit";
        }
        else
        {
            retval[sp[0]] = result;
        }
    }
    
    return retval;
}

function mturk_isassigned()
{
    var params = mturk_parameters();
    return params.assignmentid && params.assignmentid != "ASSIGNMENT_ID_NOT_AVAILABLE" && params.hitid && params.workerid;
}

function mturk_submit(callback)
{
    if (!mturk_isassigned())
    {
        alert("Please accept task before submitting.");
        return;
    }

    console.log("Preparing work for submission");

    var params = mturk_parameters();

    $("body").append('<form method="get" id="turkic_mturk">' +
        '<input type="hidden" name="assignmentId" value="">' +
        '<input type="hidden" name="data" value="" />' +
        '</form>');

    $("#turkic_mturk input").val(params.assignmentid);
    $("#turkic_mturk").attr("action", params.action);

    function redirect()
    {
        server_request("turkic_markcomplete", [params.hitid, params.assignmentid, params.workerid], function() {
            $("#turkic_mturk").submit();
        });
    }

    var now = (new Date()).getTime();
    server_request("turkic_savejobstats", [params.hitid, turkic_timeaccepted, now], function() {
        callback(redirect);
    });
}


function mturk_acceptfirst()
{
    var af = $('<div id="turkic_acceptfirst"></div>').prependTo("body")
    af.html("Remember to accept the task before working!");
}

function mturk_showstatistics()
{
    var stc = $('<div id="turkic_workerstats"><div id="turkic_workerstatscontent"></div></div>');
    st = stc.children("#turkic_workerstatscontent");

    server_workerstats(function(data) {
        st.html("");

        var reward = $('<div id="turkic_workerstatsreward"></div>');
        var amount = Math.round(data["reward"] * 100);
        var bonus = Math.round(data["bonus"] * 100);

        var rewardstr = '<div class="turkic_workerstatsnumber">' + amount + ' &cent;</div> pay';
        if (bonus > 0)
        {
            rewardstr += ' + <div class="turkic_workerstatsnumber">' + bonus + ' &cent;</div> bonus';
        }

        reward.html('Reward: ' + rewardstr);
        st.append(reward);

        if (!data["newuser"])
        {
            st.append("Your record:");

            var subm = $('<div class="turkic_workerstatsperformance"></div>');
            var submn = $('<div class="turkic_workerstatsnumber"></div>');
            submn.html(data["numsubmitted"]);
            submn.appendTo(subm);
            subm.append(" submitted");
            subm.appendTo(st);

            var accp = $('<div class="turkic_workerstatsperformance"></div>');
            var accpn = $('<div class="turkic_workerstatsnumber"></div>');
            accpn.html(data["numaccepted"]);
            accpn.appendTo(accp);
            accp.append(" accepted");
            accp.appendTo(st);

            var rejt = $('<div class="turkic_workerstatsperformance"></div>');
            var rejtn = $('<div class="turkic_workerstatsnumber"></div>');
            rejtn.html(data["numrejected"]);
            rejtn.appendTo(rejt);
            rejt.append(" rejected");
            rejt.appendTo(st);
        }
        else
        {
            st.append("<strong>Welcome new user!</strong> Please take a minute to read the instructions.");
        }
        stc.prependTo("body");
    });
}

//function worker_showtraining()
//{
//    var tr = $('<div id="turkic_training"></div>');
//    tr.appendTo("body");
//}
//
//function worker_hidetraining()
//{
//    $("#turkic_training").remove();
//}
//
//function worker_needstraining(iftrue, iffalse)
//{
//    server_workerstats(function(data) {
//        if (data["newuser"])
//        {
//            iftrue(data);
//        }
//        else if (iffalse != null)
//        {
//            iffalse(data);
//        }
//    });
//}

function server_geturl(action, parameters)
{
    var url = "server/" + action;
    for (var x in parameters)
    {
        url += "/" + parameters[x];
    }
    return url;
}

function server_request(action, parameters, callback)
{
    var url = server_geturl(action, parameters);
    console.log("Server request: " + url);
    $.ajax({
        url: url,
        dataType: "json",
        success: function(data) {
            callback(data);
        },
        error: function(xhr, textstatus) {
            console.log(xhr.responseText);
            death("Server Error");
        }
    });
}

function server_post(action, parameters, data, callback)
{
    var url = server_geturl(action, parameters);
    console.log("Server post: " + url);
    $.ajax({
        url: url,
        dataType: "json",
        type: "POST",
        data: data,
        success: function(data) {
            callback(data);
        },
        error: function(xhr, textstatus) {
            console.log(xhr.responseText);
            death("Server Error");
        }
    });
}

var server_workerstats_data = null;
function server_workerstats(callback)
{
    if (server_workerstats_data == null)
    {
        var params = mturk_parameters();
        if (params.workerid)
        {
            server_request("turkic_getworkerstats",
                [params.hitid, params.workerid],
                function (data) {
                    server_workerstats_data = data;
                    callback(data);
                });
        }
    }
    else
    {
        callback(server_workerstats_data);
    }
}

function death(message)
{
    document.write("<style>body{background-color:#333;color:#fff;text-align:center;padding-top:100px;font-weight:bold;font-size:30px;font-family:Arial;</style>" + message);
}

if (!console)
{
    var console = new Object();
    console.log = function() {};
}
