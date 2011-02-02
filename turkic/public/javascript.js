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

function mturk_isoffline()
{
    var params = mturk_parameters();
    return params.hitid == "offline";
}

function mturk_submitallowed()
{
    return mturk_isassigned() || mturk_isoffline();
}

function mturk_submit(callback)
{
    if (!mturk_submitallowed())
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
        server_request("turkic_markcomplete",
            [params.hitid, params.assignmentid, params.workerid],
            function() {
                $("#turkic_mturk").submit();
            });
    }

    if (mturk_isoffline())
    {
        callback(function() { });
    }
    else
    {
        var donateyes = $("#turkic_donate_yes").attr("checked") ? 1 : 0;
        server_request("turkic_savejobstats", [params.hitid, turkic_timeaccepted, now, donateyes], function() {
            callback(redirect);
        });
    }
}


function mturk_acceptfirst()
{
    if (mturk_isoffline())
    {
        mturk_showoffline();
    }
    else
    {
        var af = $('<div id="turkic_acceptfirst"></div>').prependTo("body")
        af.html("Remember to accept the task before working!");
    }
}

function mturk_showoffline()
{
    var stc = $('<div id="turkic_workerstats"><div id="turkic_workerstatscontent"></div></div>');
    st = stc.children("#turkic_workerstatscontent");
    st.append("Task is in <strong>offline</strong> mode. Mechanical Turk hooks are disabled.");
    stc.appendTo("body");
}

function mturk_showstatistics()
{
    var stc = $('<div id="turkic_workerstats"><div id="turkic_workerstatscontent"></div></div>');
    st = stc.children("#turkic_workerstatscontent");

    server_workerstats(function(data) {
        st.html("");

        var reward = $('<div id="turkic_workerstatsreward"></div>');
        var amount = Math.round(data["reward"] * 100);
        var donationenabled = data["donation"] == 2;
        var bonuses = data["bonuses"]

        var rewardstr = '<div class="turkic_workerstatsnumber">' + amount + ' &cent;</div> pay';

        for (var i in bonuses)
        {
            rewardstr += ' + <div class="turkic_workerstatsnumber">' + (bonuses[i][0] * 100) + ' &cent;</div> ' + bonuses[i][1];
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

        if (donationenabled && bonus > 0)
        {
            mturk_showdonate(amount, bonus);
        }
    });
}

function mturk_showdonate(reward, bonus)
{
    if ($("#turkic_donation").size())
    {
        $("#turkic_donation").show();
        $("#turkic_overlay").show();
        return;
    }
    
    $('<div id="turkic_overlay"></div>').appendTo("body");

    var str = '<h1>Do you want to end world hunger?</h1>';
    str += '<p>We are offering our users the chance to work on behalf of a charity. When your HIT is accepted, we will pay you both your standard compensation as well as a bonus. If you choose, we can donate your bonus to charity instead.</p>';
    str += '<p>For this HIT, you will receive ' + reward + '&cent; with an additional ' + bonus + '&cent; bonus. If you opt to donate, your HIT will be accepted and you will receive ' + reward + '&cent;, but we will donate your bonus to charity.</p>';
    str += '<p>We urge you to consider donating. All bonuses will go to <a href="http://www.wfp.org" target="_blank">United Nation\'s World Food Programme</a> to fight world hunger. If every worker donates, we can collectively donate hundreds of thousands of dollars. Your actions can have an impact &mdash; all you must do is donate.</p>';
    str += '<div style="margin-left : 20px;">';
    str += "<strong>Can we donate your bonus to fight world hunger?</strong><br>";
    str += '<input type="radio" id="turkic_donate_yes" name="turkic_donate_option">';
    str += '<label for="turkic_donate_yes">Yes, donate this bonus to the World Food Programme on my behalf.</label><br>';
    str += '<input type="radio" id="turkic_donate_no" name="turkic_donate_option">';
    str += '<label for="turkic_donate_no">No, I want to keep this bonus for myself.</label><br>';
    //str += '<div style="float:right;"><input type="checkbox" id="turkic_donate_notagain"> <label for="turkic_donate_notagain">Do not show again</label></div>';
    str += '<input type="button" id="turkic_donate_close" value="Continue">';
    str += '</div>';
    str += '<p>Looking for more ways to donate? Check out <a href="http://freerice.com" target="_blank">Freerice.com</a> to donate even more.</p>';
    var donation = $('<div id="turkic_donation"></div>').appendTo("body");
    donation.append(str);

    if ($.cookie("turkic_charity_previous") != null)
    {
        if ($.cookie("turkic_charity_previous") == 1)
        {
            $("#turkic_donate_yes").attr("checked", true);
        }
        else
        {
            $("#turkic_donate_no").attr("checked", true);
        }
    }

    $("#turkic_donate_close").click(function() {
        var donateyes = $("#turkic_donate_yes").attr("checked");
        var donateno  = $("#turkic_donate_no").attr("checked");

        if (!donateyes && !donateno)
        {
            window.alert("Please choose your donation option.");
            return;
        }

        $.cookie("turkic_charity_previous", donateyes ? 1 : 0);

        // we need to reset the timestamp because the task doesnt start until they continue
        turkic_timeaccepted = (new Date()).getTime();

        $("#turkic_overlay").hide();
        donation.hide();
    });
}

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
