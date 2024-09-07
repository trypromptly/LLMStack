import React, { useEffect, useState } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Typography,
  Box,
  FormControlLabel,
  Checkbox,
  Divider,
} from "@mui/material";
import { axios } from "../../data/axios";

const daysOfWeek = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

const ScheduleForm = ({
  scheduleType,
  setScheduleType,
  time,
  setTime,
  day,
  setDay,
}) => {
  return (
    <Stack spacing={3}>
      <Typography variant="body2">
        Set a schedule to automatically run this sheet.
      </Typography>
      <FormControl fullWidth>
        <InputLabel id="schedule-type-label">Schedule Type</InputLabel>
        <Select
          labelId="schedule-type-label"
          value={scheduleType}
          onChange={(e) => setScheduleType(e.target.value)}
          label="Schedule Type"
        >
          <MenuItem value="daily">Daily</MenuItem>
          <MenuItem value="weekly">Weekly</MenuItem>
        </Select>
      </FormControl>

      {/* Render time input for both daily and weekly */}
      <TextField
        label="Time"
        type="time"
        value={time}
        onChange={(e) => setTime(e.target.value)}
        InputLabelProps={{ shrink: true }}
        fullWidth
      />

      {/* Render day input only for weekly schedule */}
      {scheduleType === "weekly" && (
        <FormControl fullWidth>
          <InputLabel id="day-label">Day of the Week</InputLabel>
          <Select
            labelId="day-label"
            value={day}
            onChange={(e) => setDay(e.target.value)}
            label="Day of the Week"
          >
            {daysOfWeek.map((d) => (
              <MenuItem key={d} value={d}>
                {d}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
    </Stack>
  );
};

const ScheduleRunsModal = ({ open, onClose, sheetUuid }) => {
  const [existingSchedule, setExistingSchedule] = useState(null);

  const [scheduleType, setScheduleType] = useState(
    existingSchedule?.type || "daily",
  );
  const [time, setTime] = useState(existingSchedule?.time || "");
  const [day, setDay] = useState(existingSchedule?.day || "");

  const [deleteSchedule, setDeleteSchedule] = useState(false);

  useEffect(() => {
    if (open) {
      axios()
        .get(`/api/sheets/${sheetUuid}`)
        .then((response) => {
          setExistingSchedule(response.data?.scheduled_run_config);
        });
    }
  }, [setExistingSchedule]);

  const handleSave = () => {
    let schedule_config = null;
    if (existingSchedule && deleteSchedule) {
      // Delete existing schedule
      schedule_config = null;
    } else if (!existingSchedule) {
      // Create new schedule
      schedule_config = {
        type: scheduleType,
        time,
        ...(scheduleType === "weekly" && { day }),
      };
    }
    axios()
      .patch(`/api/sheets/${sheetUuid}`, {
        scheduled_run_config: schedule_config,
      })
      .then(onClose);
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Automated Runs</DialogTitle>
      <DialogContent>
        {existingSchedule ? (
          <Box mt={3}>
            <Typography variant="h6">Current Schedule:</Typography>
            <Typography>
              Type: <strong>{existingSchedule.type}</strong>
            </Typography>
            <Typography>
              Time: <strong>{existingSchedule.time}</strong>
            </Typography>
            {existingSchedule.type === "weekly" && (
              <Typography>
                Day: <strong>{existingSchedule.day}</strong>
              </Typography>
            )}
            <Divider />
            <FormControlLabel
              control={
                <Checkbox
                  checked={deleteSchedule}
                  onChange={(e) => setDeleteSchedule(e.target.checked)}
                />
              }
              label="Delete existing schedule"
            />
            {deleteSchedule && (
              <Typography variant="body2" color="error">
                You have selected to delete the current schedule.
              </Typography>
            )}
          </Box>
        ) : (
          <ScheduleForm
            scheduleType={scheduleType}
            setScheduleType={setScheduleType}
            time={time}
            setTime={setTime}
            day={day}
            setDay={setDay}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSave}>Save</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ScheduleRunsModal;
