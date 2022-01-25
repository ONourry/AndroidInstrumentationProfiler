package fr.neamar.kiss.androidTest;

// import androidx.test.runner.AndroidJUnitRunner;
// import android.support.test.runner.AndroidJUnitRunner;

import android.os.Bundle;
import android.util.Log;

import android.app.Activity;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;

public class MyRunner extends AndroidJUnitRunner {
    @Override
    public void callActivityOnStart(Activity activity) {
        Log.d("PETRA", "START_PROFILING_NOW");
        try {
         Thread.sleep(5000);
        } catch (InterruptedException e) {
        }
        super.callActivityOnStart(activity);
    }


    @Override
    protected void restoreUncaughtExceptionHandler() {
        Log.d("PETRA", "STOP_PROFILING_NOW");
        try {
            Thread.sleep(5000);
        } catch (InterruptedException e) {
        }
        super.restoreUncaughtExceptionHandler();
    }

}