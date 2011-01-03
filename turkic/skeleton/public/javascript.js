$(document).ready(function()
{
    if (!mturk_isassigned())
    {
        mturk_acceptfirst();
    }
    else
    {
        worker_showstatistics();
    }
});
