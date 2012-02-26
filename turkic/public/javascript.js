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

function mturk_ready(callback)
{
    console.log("Waiting to be ready");
    if (mturk_isassigned())
    {
        server_jobstats(function() {
            console.log("Ok, ready");
            callback();
        });
    }
    else
    {
        console.log("Ok, ready, but no stats");
        callback();
    }
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
        server_request("turkic_savejobstats", 
            [params.hitid, turkic_timeaccepted, now], 
            function() {
                mturk_showdonate(function() {
                    eventlog_save(function() {
                        $("#turkic_mturk").submit();
                    });
                });
            });
    }

    if (mturk_isoffline())
    {
        callback(function() { });
    }
    else
    {
        server_request("turkic_markcomplete",
            [params.hitid, params.assignmentid, params.workerid],
            function() {
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

    st.append(mturk_setuptimer());

    st.append("Task is in <strong>offline</strong> mode.");

    stc.appendTo("body");
}

function mturk_setuptimer()
{
    var timer = $('<div id="turkic_timer"></div>');
    var button = $('<input type="button" value="Start Timer" id="turkic_timer_button">').appendTo(timer);
    var tvalue = $('<div id="turkic_timer_value">0m 00s</div>').appendTo(timer);

    var interval = null;
    var secondspassed = 0;

    button.toggle(function() {
        $(this).val("Stop Timer"); 

        interval = window.setInterval(function() {
            secondspassed++;

            var m = Math.floor(secondspassed / 60);
            var s = secondspassed % 60;

            if ((s + "").length == 1)
            {
                s = "0" + s;
            }

            var str = m + "m " + s + "s";

            tvalue.html(str);
        }, 1000);
    }, function() {
        $(this).val("Start Timer"); 

        window.clearInterval(interval);
        interval = null;
    });

    return timer;
}

function mturk_disabletimer()
{
    $("#turkic_timer input").attr("disabled", "disabled");
}

function mturk_enabletimer()
{
    $("#turkic_timer input").attr("disabled", "");
}

function mturk_showstatistics()
{
    console.log("Showing statistics");

    var stc = $('<div id="turkic_workerstats"><div id="turkic_workerstatscontent"></div></div>');
    st = stc.children("#turkic_workerstatscontent");

    server_jobstats(function(data) {
        st.html("");

        var reward = $('<div id="turkic_workerstatsreward"></div>');
        var amount = Math.round(data["reward"] * 100);
        var bonuses = data["bonuses"]

        var rewardstr = '<div class="turkic_workerstatsnumber">' + amount + ' &cent;</div> pay';

        for (var i in bonuses)
        {
            rewardstr += ' + <div class="turkic_workerstatsnumber">' + Math.round(bonuses[i][0] * 100) + ' &cent;</div> ' + bonuses[i][1];
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

function mturk_blockbadworkers(callback)
{
    if (mturk_isassigned())
    {
        console.log("Checking if worker is blocked...");
        server_jobstats(function(data) {
            if (data["blocked"])
            {
                console.log("Worker is bad");
                death("You are blocked.");
            }
            else
            {
                callback();
            }
        });
    }
    else
    {
        callback();
    }
}

function mturk_showdonate(callback)
{
    var str = '<a title="Help end child hunger" href="https://www.wfp.org/' +
              'donate/fillthecup?utm_medium=banner&utm_campaign=bb-fillthe' + 
              'cup125x125" target="_blank"><img width="125" height="125" a' +
              'lt="Help end child hunger" src="http://www.wfp.org/sites/de' +
              'fault/files/125x125_fill_the_cup.jpg" align="right" /></a>';
    str += "<h1>Help us end world hunger.</h1>" +
           "<p>We are offering you the chance to work on behalf of " +
           "the United Nation's World Food Programme. When your HIT is " +
           "accepted, we will pay you both your standard compensation as " +
           "well as a bonus. If you choose, we can donate part of your " +
           "bonus to charity instead.</p>" +
           "<p>If every worker donates, we can collectively donate " +
           "hundreds of thousands of dollars. 25&cent; will feed a " +
           "hungry schoolchild enough nutritious food for a day. $50 can " +
           "feed a child for an entire year. Your work can have an " +
           "impact &mdash; all you must do is donate.</p>";

    str += "<p style='margin-left:30px;'>";
    str += "<strong>How much do you wish to donate?</strong><br>";
    str += "<input type='radio' name='donateamt' id='donate0' value='0'>";
    str += "<label for='donate0'><strong>None</strong>: I want to keep ";
    str += "all of my bonus.</label><br>";
    str += "<input type='radio' name='donateamt' id='donate50' value='.5' ";
    str += "checked='checked'>";
    str += "<label for='donate50'><strong>Half</strong>: I wish to donate half of my ";
    str += "bonus and keep the other half.</label><br>";
    str += "<input type='radio' name='donateamt' id='donate100' value='1'>";
    str += "<label for='donate100'><strong>All</strong>: Please donate my bonus to fight world hunger.</label><br>";
    str += "<input type='button' id='turkic_donate_close' value='Submit HIT'>";
    str += "</p>";

    str += "<p>See which other workers are donating and where you rank on our <a href='http://deepthought.ics.uci.edu/~cvondrick/donation/' target='_blank'>status page</a>.</p>";


    server_jobstats(function(data) {
        if (data["donationcode"] == 0 || data["bonuses"].length == 0)
        {
            callback();
            return;
        }

        console.log("Show donation")
        var overlay = $('<div id="turkic_overlay"></div>').appendTo("body");

        var donation = $('<div id="turkic_donation"></div>').appendTo("body");
        donation.append(str);

        $("#turkic_donate_close").click(function() {
            var amount = $("input[name=donateamt]:checked").val();
            var params = mturk_parameters();
            server_request("turkic_savedonationstatus", [params.hitid, amount],
                            function() {
                                overlay.remove();
                                donation.remove();
                                callback();
                            });
        });
    });
}

function worker_isverified(iftrue, iffalse)
{
    if (mturk_isassigned())
    {
        server_jobstats(function(data) {
            if (data["verified"])
            {
                iftrue();
            }
            else
            {
                iffalse();
            }
        });
    }
    else
    {
        // not accepted, so assume verified to create illusion
        iftrue();
    }
}


var turkic_event_log = [];
function eventlog(domain, message)
{
    var timestamp = (new Date()).getTime();
    turkic_event_log.push([timestamp, domain, message]);
    //console.log(timestamp + " " + domain + ": " + message);
}

function eventlog_save(callback)
{
    if (mturk_submitallowed())
    {
        var params = mturk_parameters();
        var data = "[";
        var counter = 0;
        for (var i in turkic_event_log)
        {
            data += "[" + turkic_event_log[i][0] + ",";
            data += "\"" + turkic_event_log[i][1] + "\",";
            data += "\"" + turkic_event_log[i][2] + "\"],";
            counter++;
        }
        if (counter == 0)
        {
            callback();
            return;
        }

        data = data.substr(0, data.length - 1) + "]";
        console.log(data);
        server_post("turkic_saveeventlog", [params.hitid], data, function() {
            callback();
        });
    }
    else
    {
        callback();
    }
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

var server_jobstats_data = null;
function server_jobstats(callback)
{
    if (server_jobstats_data == null)
    {
        console.log("Querying for job stats");
        var params = mturk_parameters();
        if (params.workerid)
        {
            server_request("turkic_getjobstats",
                [params.hitid, params.workerid],
                function (data) {
                    server_jobstats_data = data;
                    callback(data);
                });
        }
        else
        {
            death("Job stats unavailable");
        }
    }
    else
    {
        callback(server_jobstats_data);
    }
}

function death(message)
{
    console.log(message);
    document.write("<style>body{background-color:#333;color:#fff;text-align:center;padding-top:100px;font-weight:bold;font-size:30px;font-family:Arial;</style>" + message);
}

if (!console)
{
    var console = new Object();
    console.log = function() {};
    console.dir = function() {};
}
