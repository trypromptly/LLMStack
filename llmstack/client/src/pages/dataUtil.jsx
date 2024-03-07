const getCookie = (name) => {
  const cookieValue = document.cookie
    .split(";")
    .find((cookie) => cookie.trim().startsWith(`${name}=`));
  if (!cookieValue) return null;
  return cookieValue.split("=")[1];
};

export const postData = async (url, data, loadingCb, responseCb, errorCb) => {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(data),
    });
    const json = await response.json();
    responseCb(json);
    loadingCb(false);
  } catch (e) {
    errorCb(e.message);
    loadingCb(false);
  }
};
