export function LocaleDate(props) {
  const date = new Date(props.value);
  return <span>{date.toLocaleString()}</span>;
}

// Render file size in human readable format
export function FileSize(props) {
  let size = props.value;
  const units = ["", "K", "M", "G", "T", "P", "E", "Z", "Y"];
  let unit = 0;
  while (size >= 1024) {
    size /= 1024;
    unit += 1;
  }
  return (
    <span>
      {size > 0
        ? size.toFixed(2) + " " + units[unit]
        : size + " " + units[unit]}
    </span>
  );
}
