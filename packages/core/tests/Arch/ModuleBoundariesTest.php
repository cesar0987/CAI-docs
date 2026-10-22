<?php

declare(strict_types=1);

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\DB;

/*
|--------------------------------------------------------------------------
| Arch Tests — Fronteras entre módulos (Proyecto CAI)
|--------------------------------------------------------------------------
| Ver: sistema cai/02 - Arquitectura/02.03 Reglas de Frontera entre Módulos.md
| Ver: sistema cai/05 - Proceso de Desarrollo/05.05 Estrategia de Pruebas.md §4
|
| Estas reglas son normativas. Si rompen, la CI falla.
*/

describe('Reglas de frontera entre módulos', function () {
    it('A-01: no importa modelos de otro módulo', function () {
        $modules = [
            'Cai\\Billing',
            'Cai\\Care',
            'Cai\\Documents',
            'Cai\\Identity',
            'Cai\\Notifications',
            'Cai\\Reporting',
            'Cai\\Scheduling',
            'Cai\\Students',
        ];

        foreach ($modules as $module) {
            expect($module)->not->toUse([
                'Cai\\Billing\\Models',
                'Cai\\Care\\Models',
                'Cai\\Documents\\Models',
                'Cai\\Identity\\Models',
                'Cai\\Notifications\\Models',
                'Cai\\Reporting\\Models',
                'Cai\\Scheduling\\Models',
                'Cai\\Students\\Models',
            ]);
        }
    });

    it('A-02: ninguna relación Eloquent cruza módulos', function () {
        expect('Cai\\Billing\\Models\\Charge')->not->toUse('Cai\\Students\\Models\\Student');
        expect('Cai\\Billing\\Models\\Charge')->not->toUse('Cai\\Scheduling\\Models\\Session');
        expect('Cai\\Care\\Models\\ClinicalNote')->not->toUse('Cai\\Billing\\Models\\Payment');
        expect('Cai\\Care\\Models\\ClinicalNote')->not->toUse('Cai\\Students\\Models\\Student');
        expect('Cai\\Documents\\Models\\Document')->not->toUse('Cai\\Billing\\Models\\Charge');
        expect('Cai\\Notifications\\Models\\Notification')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
    });

    it('A-03: los eventos no contienen modelos Eloquent', function () {
        expect('Cai\\Billing\\Events')->not->toUse(Model::class);
        expect('Cai\\Care\\Events')->not->toUse(Model::class);
        expect('Cai\\Documents\\Events')->not->toUse(Model::class);
        expect('Cai\\Identity\\Events')->not->toUse(Model::class);
        expect('Cai\\Notifications\\Events')->not->toUse(Model::class);
        expect('Cai\\Reporting\\Events')->not->toUse(Model::class);
        expect('Cai\\Scheduling\\Events')->not->toUse(Model::class);
        expect('Cai\\Students\\Events')->not->toUse(Model::class);
    });

    it('A-04: los eventos no contienen datos clínicos', function () {
        // Los eventos de otros módulos NO deben hacer referencia a ClinicalNote
        expect('Cai\\Billing\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
        expect('Cai\\Billing\\Events')->not->toUse('Cai\\Care\\DTO');
        expect('Cai\\Documents\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
        expect('Cai\\Notifications\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
        expect('Cai\\Reporting\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
        expect('Cai\\Scheduling\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
        expect('Cai\\Students\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
        expect('Cai\\Identity\\Events')->not->toUse('Cai\\Care\\Models\\ClinicalNote');
    });

    it('A-05: la lógica de negocio no está en Filament', function () {
        // Las clases de Filament NO deben acceder a la base de datos directamente
        expect('Cai\\Billing\\Filament')->not->toUse(DB::class);
        expect('Cai\\Care\\Filament')->not->toUse(DB::class);
        expect('Cai\\Documents\\Filament')->not->toUse(DB::class);
        expect('Cai\\Identity\\Filament')->not->toUse(DB::class);
        expect('Cai\\Notifications\\Filament')->not->toUse(DB::class);
        expect('Cai\\Reporting\\Filament')->not->toUse(DB::class);
        expect('Cai\\Scheduling\\Filament')->not->toUse(DB::class);
        expect('Cai\\Students\\Filament')->not->toUse(DB::class);
    });

    it('A-06: no hay DB::raw en el código de aplicación', function () {
        expect('Cai\\Core')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Identity')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Students')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Scheduling')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Care')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Billing')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Documents')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Notifications')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
        expect('Cai\\Reporting')->not->toUse('Illuminate\\Support\\Facades\\DB::raw');
    });

    it('A-07: los modelos Eloquent están en src/Models de su paquete', function () {
        expect('App\\Models')->not->toBeUsed();
    });

    it('A-08: reporting solo lee de forma agregada (sin modelos clínicos)', function () {
        // Reporting NO debe importar modelos directamente desde Care
        expect('Cai\\Reporting')->not->toUse('Cai\\Care\\Models');
    });

    it('A-09: care no es usado por módulos no autorizados', function () {
        // Módulos que NO deben importar nada de Care (excepto contratos si se justifica con ADR)
        expect('Cai\\Students')->not->toUse('Cai\\Care\\Models');
        expect('Cai\\Students')->not->toUse('Cai\\Care\\Actions');
        expect('Cai\\Students')->not->toUse('Cai\\Care\\Services');
        expect('Cai\\Scheduling')->not->toUse('Cai\\Care\\Models');
        expect('Cai\\Documents')->not->toUse('Cai\\Care\\Models');
        expect('Cai\\Notifications')->not->toUse('Cai\\Care\\Models');
    });

    it('A-10: core no depende de paquetes de negocio', function () {
        expect('Cai\\Core')->not->toUse([
            'Cai\\Identity\\',
            'Cai\\Students\\',
            'Cai\\Scheduling\\',
            'Cai\\Care\\',
            'Cai\\Billing\\',
            'Cai\\Documents\\',
            'Cai\\Notifications\\',
            'Cai\\Reporting\\',
        ]);
    });
});
