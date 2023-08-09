// Helper function to stitch two objects together. If the key doesn't exist in the first object, it will be added. If it does exist, the value will be appended to the existing value in case of strings. In case of arrays, entries will be recursively stitched together. We keep the original order of the array. If the incoming array has more entries than the existing array, the extra entries will be appended to the end of the existing array.
export function stitchObjects(obj1, obj2) {
  if (!obj1) return obj2;
  if (!obj2) return obj1;

  let newObj = { ...obj1 };

  for (const [key, value] of Object.entries(obj2)) {
    // If the key doesn't exist in the first object, add it
    if (!newObj[key]) {
      newObj[key] = value;
      continue;
    }

    // If the key exists in the first object, stitch the values together
    if (Array.isArray(value)) {
      if (Array.isArray(newObj[key])) {
        // If both the values are arrays, stitch the arrays together
        for (let i = 0; i < value.length; i++) {
          if (i < newObj[key].length) {
            if (typeof value[i] === "string") {
              newObj[key][i] = newObj[key][i] + value[i];
              continue;
            }
            if (typeof value[i] === "number") {
              newObj[key][i] = value[i];
              continue;
            }
            // If the index exists in the existing array, stitch the objects together
            newObj[key][i] = stitchObjects(newObj[key][i], value[i]);
          } else {
            // If the index doesn't exist in the existing array, append the object to the end of the array
            newObj[key].push(value[i]);
          }
        }
      } else {
        newObj[key] = newObj[key] + value;
      }
    } else if (typeof value === "object") {
      newObj[key] = stitchObjects(newObj[key], value);
    } else {
      newObj[key] = newObj[key] + value;
    }
  }
  return newObj;
}
