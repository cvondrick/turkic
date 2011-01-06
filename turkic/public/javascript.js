var wordsofwisdom = ["Great job!",
                     "Keep up the good work!",
                     "Fantastic!",
                     "Excellent!",
                     "Thanks for your work!"]

var turkic_timeaccepted = (new Date()).getTime();

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
    var now = (new Date()).getTime();

    $("body").append('<form method="get" id="turkic_mturk">' +
        '<input type="hidden" name="assignmentId" value="">' +
        '<input type="hidden" name="data" value="" />' +
        '</form>');

    $("#turkic_mturk input").val(params.assignmentid);
    $("#turkic_mturk").attr("action", params.action);
        
    // function that must be called to formally complete transaction
    function redirect()
    {
        server_request("turkic_markcomplete", [params.hitid, params.assignmentid, params.workerid], function() {
            $("#turkic_mturk").submit();
        });
    }

    // ask for donation
    $('<div id="turkic_overlay"></div>').appendTo("body");

    var str = '<h1>You have the option to donate your bonus.</h1>';
    str += '<p>Congratulations! You have <strong>earned a one cent bonus</strong> as a reward for your hard work.</p>';
    str += '<p>We are giving workers the option to donate their bonus to a charity. Instead of taking the one cent for yourself, consider donating it. ';
    str += 'If every worker donates, together we can collectively donate <strong>hundreds of thousands of dollars</strong>. ';
    str += 'If you choose to donate, we will pass your bonus on to Wikipedia to support open access to information on the web.</p>';
    str += '<div style="margin-left : 20px;">';
    str += '<input type="radio" id="turkic_donate_yes" name="turkic_donate_option">';
    str += '<label for="turkic_donate_yes">Please donate this bonus to charity on my behalf.</label><br>';
    str += '<input type="radio" id="turkic_donate_no" name="turkic_donate_option">';
    str += '<label for="turkic_donate_no">I want to keep this bonus for myself.</label><br>';
    str += '<input type="button" id="turkic_donate_submit" value="Submit HIT">';
    str += '</div>';
    str += '<p>If you would like to suggest a possible future charity, please do not hesistate to contact us.</p>';
    var donation = $('<div id="turkic_donation"></div>').appendTo("body");
    donation.append(str);

    $("#turkic_donate_submit").click(function() {
        var donateyes = $("#turkic_donate_yes").attr("checked");
        var donateno = $("#turkic_donate_no").attr("checked");

        if (!donateyes && !donateno)
        {
            window.alert("Please select your reward option.");
            return;
        }

        var donateyes = donateyes ? 1 : 0;
        server_request("turkic_savejobstats", [params.hitid, turkic_timeaccepted, now, donateyes], function() {
            callback(redirect);
        });
    });
}


function mturk_acceptfirst()
{
    var af = $('<div id="turkic_acceptfirst"></div>').prependTo("body")
    af.html("Remember to accept the task before working!");
}

function worker_showstatistics()
{
    var stc = $('<div id="turkic_workerstatus"><div id="turkic_workerstatuscontent"></div></div>');
    st = stc.children("#turkic_workerstatuscontent");

    server_workerstatus(function(data) {
        st.html("");
        if (!data["newuser"])
        {
            if (data["numaccepted"] >= 5 && data["numaccepted"] > data["numrejected"])
            {
                var wisdom = $('<div id="turkic_workerstatuswisdom"></div>');
                var randwisdom = Math.floor(wordsofwisdom.length * Math.random());
                wisdom.html(wordsofwisdom[randwisdom]);
                st.append(wisdom);
            }

            st.append("Your record:");

            var subm = $('<div class="turkic_workerstatusnumber"></div>');
            subm.html(data["numsubmitted"]);
            subm.appendTo(st);
            st.append("submitted");

            var accp = $('<div class="turkic_workerstatusnumber"></div>');
            accp.html(data["numaccepted"]);
            accp.appendTo(st);
            st.append("accepted");

            var rejt = $('<div class="turkic_workerstatusnumber"></div>');
            rejt.html(data["numrejected"]);
            rejt.appendTo(st);
            st.append("rejected");
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
//    server_workerstatus(function(data) {
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

var server_workerstatus_data = null;
function server_workerstatus(callback)
{
    if (server_workerstatus_data == null)
    {
        var params = mturk_parameters();
        if (params.workerid)
        {
            server_request("turkic_getworkerstatus",
                {"workerid": params.workerid},
                function (data) {
                    server_workerstatus_data = data;
                    callback(data);
                });
        }
    }
    else
    {
        callback(server_workerstatus_data);
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
