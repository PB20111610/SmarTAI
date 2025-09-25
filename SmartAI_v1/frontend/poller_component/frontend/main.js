// (这个文件的内容和上一回答中的完全一样)
function onRender(event) {
  const { jobs_json, backend_url } = event.detail.args;
  const backend = backend_url.rstrip("/");
  let jobsData;

  try {
    jobsData = JSON.parse(jobs_json);
  } catch (e) {
    console.error("无法解析任务数据对象:", e);
    jobsData = {};
  }

  const jobIds = Object.keys(jobsData);
  if (jobIds.length === 0) {
    return;
  }

  const startPollingForJob = (jobId, taskDetails) => {
    const completedKey = `job-completed-${jobId}`;
    if (sessionStorage.getItem(completedKey)) {
      return;
    }

    const intervalId = setInterval(async () => {
      try {
        const resp = await fetch(backend + '/ai_grading/grade_result/' + jobId);
        if (!resp.ok) return;

        const data = await resp.json();
        if (data && data.status === 'completed') {
          clearInterval(intervalId);
          if (!sessionStorage.getItem(completedKey)) {
            const taskName = taskDetails.name || "未命名任务";
            const submittedAt = taskDetails.submitted_at || "未知时间";
            alert(`您于 [${submittedAt}] 提交的任务\n"${taskName}"\n已成功完成！`);
            sessionStorage.setItem(completedKey, 'true');
            Streamlit.setComponentValue({ "rerun": true, "timestamp": Date.now() });
          }
        }
      } catch (err) {}
    }, 3000);
  };

  jobIds.forEach(jobId => {
    startPollingForJob(jobId, jobsData[jobId]);
  });
}

String.prototype.rstrip = function(chars) {
    let regex = new RegExp(chars + "+$", "i");
    return this.replace(regex, "");
};

Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();